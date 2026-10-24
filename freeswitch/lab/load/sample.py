#!/usr/bin/env python3
"""LAB ONLY. Samples, once a second, the CPU (utime+stime, all threads) and
resident memory of the lab FreeSWITCH and the far-end FreeSWITCH processes,
and the whole machine's CPU, until killed.
  usage: sample.py <fs_host_pid> <far_host_pid> <out.csv>"""
import os, sys, time
fs, far, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
HZ = os.sysconf("SC_CLK_TCK")


def proc(pid):
    with open("/proc/%d/stat" % pid) as f:
        parts = f.read().rsplit(")", 1)[1].split()
    cpu = (int(parts[11]) + int(parts[12])) / HZ
    rss = 0
    with open("/proc/%d/status" % pid) as f:
        for line in f:
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1]) * 1024
    threads = len(os.listdir("/proc/%d/task" % pid))
    return cpu, rss, threads


def host():
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    return sum(v) / HZ, (v[3] + v[4]) / HZ


new = not os.path.exists(out)
with open(out, "a") as o:
    if new:
        o.write("t,fs_cpu_s,fs_rss,fs_threads,far_cpu_s,far_rss,host_total_s,host_idle_s\n")
    while True:
        try:
            a, b = proc(fs), proc(far)
        except FileNotFoundError:
            break
        h = host()
        o.write("%.3f,%.3f,%d,%d,%.3f,%d,%.3f,%.3f\n" % (time.time(), a[0], a[1], a[2], b[0], b[1], h[0], h[1]))
        o.flush()
        time.sleep(1)
