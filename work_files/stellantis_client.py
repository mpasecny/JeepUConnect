#!/usr/bin/env python3
"""
Stellantis / Fiat (Uconnect) example client using `py-uconnect`.

This script attempts to import and use the `py_uconnect` client in a
robust way (works if methods are synchronous or asynchronous).

Usage:
  pip install -r requirements.txt
  python stellantis_client.py --username YOU@EMAIL --password SECRET [--vehicle-id VIN]

It will try to authenticate, refresh data and print discovered vehicles or vehicle state.
"""
import argparse
import asyncio
import inspect
import sys
from py_uconnect import brands, Client

IMPORT_ERROR = None
ClientClass = None
try:
    # recommended package name is `py_uconnect` (installed via pip install py-uconnect)
    from py_uconnect.client import Client as ClientClass
except Exception as e:  # pragma: no cover - runtime dependency
    IMPORT_ERROR = e


def instantiate_client(cls, username, password, **kwargs):
    """Try several constructor signatures to create the client instance."""
    if cls is None:
        raise RuntimeError(f"py_uconnect import failed: {IMPORT_ERROR}")

    try:
        return cls(username, password, **kwargs)
    except TypeError:
        # try common alternative keyword names
        try:
            return cls(username=username, password=password, **kwargs)
        except Exception:
            # last resort: try only username (some clients accept an Account object)
            try:
                return cls(username)
            except Exception as exc:
                raise RuntimeError("Unable to construct py_uconnect Client: " + str(exc))


async def run_async_flow(client):
    """Attempt to call common async methods if available."""
    # Common lifecycle: login/authenticate -> refresh -> read vehicles
    for method_name in ("login", "authenticate", "auth", "refresh"):
        if hasattr(client, method_name):
            meth = getattr(client, method_name)
            if inspect.iscoroutinefunction(meth):
                await meth()
            else:
                # may return awaitable
                res = meth()
                if inspect.isawaitable(res):
                    await res

    # try list_vehicles or vehicles attribute
    vehicles = None
    if hasattr(client, "list_vehicles"):
        lv = getattr(client, "list_vehicles")
        res = lv()
        if inspect.isawaitable(res):
            vehicles = await res
        else:
            vehicles = res
    elif hasattr(client, "vehicles"):
        vehicles = getattr(client, "vehicles")

    return vehicles


def run_sync_flow(client):
    """Attempt to call common synchronous methods if available."""
    for method_name in ("login", "authenticate", "auth", "refresh"):
        if hasattr(client, method_name):
            meth = getattr(client, method_name)
            try:
                res = meth()
                if inspect.isawaitable(res):
                    # caller didn't expect async; run it
                    asyncio.run(res)
            except TypeError:
                # couldn't call; skip
                pass

    if hasattr(client, "list_vehicles"):
        try:
            return client.list_vehicles()
        except Exception:
            return None
    if hasattr(client, "vehicles"):
        return getattr(client, "vehicles")
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--vehicle-id", required=False)
    parser.add_argument("--region", required=False, default=None)
    args = parser.parse_args()

    if ClientClass is None:
        print("Error: py_uconnect is not installed or failed to import.")
        print("Import error:", IMPORT_ERROR)
        print("Install: pip install py-uconnect")
        sys.exit(2)

    # Build kwargs for constructor if region provided
    ctor_kwargs = {}
    if args.region:
        ctor_kwargs["region"] = args.region

    client = instantiate_client(ClientClass, args.username, args.password, **ctor_kwargs)

    # If the client object is asynchronous (methods are coroutines), run async flow
    # We detect this by checking if any common method is a coroutine function
    is_async = False
    for name in ("login", "authenticate", "refresh"):
        if hasattr(client, name) and inspect.iscoroutinefunction(getattr(client, name)):
            is_async = True
            break

    vehicles = None
    if is_async:
        vehicles = asyncio.run(run_async_flow(client))
    else:
        vehicles = run_sync_flow(client)

    print("Discovered vehicles / data:")
    print(vehicles)


if __name__ == "__main__":
    main()
