"""route_to_queue must drop its DTMF-0 callback binding on every path out.

argv: path/to/scripts/api/app.py   Exit 0 = pass.

An inbound caller in a ring group with callback enabled gets

    bind_digit_action queue,0,exec:python,api.callback_optin <id>
    digit_action_set_realm queue

on their own leg. The dmachine that holds it lives in session->dmachine[] and
is freed only when the session is destroyed (switch_core_session.c); nothing
in switch_ivr.c clears it on uuid_transfer. So the binding outlives the queue
unless the script clears it.

That mattered on the secure-payment path: the CRM transfers that same
customer leg into the `secure_payment` extension, every DTMF goes through
switch_channel_queue_dtmf -> switch_core_session_recv_dtmf, which feeds the
dmachine and swallows the key, and a matching "0" fires callback_optin, which
POSTs a queue-callback request and hangs the customer up mid-card (the
runbook's own B1 values contain a 0: expiry 1230, ZIP 78704). Lab P26.

dialplan/default/10_secure_payment.xml now runs `clear_digit_action all`
before anything else, which is the fix that actually protects card entry
(dialplan_test.py checks it). This file checks the other half: the binding is
also dropped here, on the answered path, not only on the orbit-timeout path,
so it never outlives the queue on any route out.
"""
import ast
import sys

src = open(sys.argv[1], encoding="utf-8").read()
tree = ast.parse(src)
fails = []


def calls_clear(nodes):
    """Does this straight-line block execute clear_digit_action?"""
    for n in nodes:
        for sub in ast.walk(n):
            if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                    and sub.func.attr == "execute" and sub.args
                    and isinstance(sub.args[0], ast.Constant)
                    and sub.args[0].value == "clear_digit_action"):
                return True
    return False


fn = next((f for f in ast.walk(tree)
           if isinstance(f, ast.FunctionDef) and f.name == "route_to_queue"), None)
if fn is None:
    fails.append("no route_to_queue in app.py")
else:
    binds = [s for s in ast.walk(fn)
             if isinstance(s, ast.Call) and isinstance(s.func, ast.Attribute)
             and s.func.attr == "execute" and s.args
             and isinstance(s.args[0], ast.Constant)
             and s.args[0].value == "bind_digit_action"]
    if not binds:
        fails.append("route_to_queue no longer binds a digit action; this test is stale")

    # every `return True` inside route_to_queue that is reached after the
    # fifo has been entered must have cleared the binding first
    fifo_line = next((s.lineno for s in ast.walk(fn)
                      if isinstance(s, ast.Call) and isinstance(s.func, ast.Attribute)
                      and s.func.attr == "execute" and s.args
                      and isinstance(s.args[0], ast.Constant)
                      and s.args[0].value == "fifo"), None)
    if fifo_line is None:
        fails.append("route_to_queue no longer enters the fifo; this test is stale")
    else:
        # the branches after the fifo: each `if` whose body ends in a return
        after = [s for s in fn.body if getattr(s, "lineno", 0) > fifo_line]
        exits = [s for s in after if isinstance(s, ast.If)]
        if len(exits) < 2:
            fails.append("expected at least the answered and the timeout branch after "
                         "the fifo, found %d" % len(exits))
        for br in exits:
            returns = [n for n in ast.walk(br) if isinstance(n, ast.Return)]
            if not returns:
                continue
            if not calls_clear(br.body):
                fails.append("the branch at line %d leaves route_to_queue without "
                             "clear_digit_action: the callback binding outlives the queue "
                             "on this path" % br.lineno)

for f in fails:
    print("FAIL " + f)
print("queue_binding_test: %d failed" % len(fails))
sys.exit(1 if fails else 0)
