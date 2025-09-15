#!/usr/bin/env python3
import sys, shlex

BIONET_INIT=False
TITAN_SEALED=False
TITAN_CLONES=0

def status():
    s = "online"
    print(f"STATUS: {s} | bionet: {'ready' if BIONET_INIT else 'idle'} | titan: clones={TITAN_CLONES}, sealed={'yes' if TITAN_SEALED else 'no'}")

def bionet_init():
    global BIONET_INIT
    BIONET_INIT=True
    print("BioNet: initialized (bootstrap mock)")

def titan_clone(n):
    global TITAN_CLONES
    TITAN_CLONES += n
    print(f"Titan: created {n} clone(s) → total={TITAN_CLONES} (bootstrap mock)")

def titan_seal():
    global TITAN_SEALED
    TITAN_SEALED=True
    print("Titan: failsafe SEAL engaged (bootstrap mock)")

def main():
    print("Sofia Sentinel v1.0 — bootstrap console. Type: status | bionet init | titan clone <N> | titan failsafe seal | quit")
    while True:
        try:
            line = input("sentinel> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye"); return
        if not line:
            continue
        args = shlex.split(line)
        cmd = args[0].lower()

        if cmd in ("exit","quit"):
            print("bye"); return

        elif cmd == "status":
            status()

        elif cmd == "bionet" and len(args)>=2 and args[1].lower()=="init":
            bionet_init()

        elif cmd == "titan" and len(args)>=2:
            sub = args[1].lower()
            if sub=="clone":
                try:
                    n = int(args[2]) if len(args)>=3 else 1
                except Exception:
                    print("usage: titan clone <N>"); continue
                titan_clone(n)
            elif sub=="failsafe" and len(args)>=3 and args[2].lower()=="seal":
                titan_seal()
            else:
                print("usage: titan clone <N> | titan failsafe seal")

        else:
            print("unknown command:", line)

if __name__ == "__main__":
    main()
