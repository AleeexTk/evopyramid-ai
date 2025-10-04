from __future__ import annotations
import asyncio, sys
from apps.core.integration.collective_mind import CollectiveMindV1

async def main():
    cm = CollectiveMindV1()
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "meta_agi: разработай протокол согласования ролей"
    result = await cm.run(query)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())

