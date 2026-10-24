#include <lua5.2/lua.h>
#include <lua5.2/lauxlib.h>
#include <lua5.2/lualib.h>
#include <stdio.h>
int main(int argc, char **argv) {
  lua_State *L = luaL_newstate(); luaL_openlibs(L);
  lua_newtable(L);
  for (int i = 2; i < argc; i++) { lua_pushstring(L, argv[i]); lua_rawseti(L, -2, i - 1); }
  lua_setglobal(L, "arg");
  if (luaL_dofile(L, argv[1])) { fprintf(stderr, "%s\n", lua_tostring(L, -1)); return 1; }
  return 0;
}
