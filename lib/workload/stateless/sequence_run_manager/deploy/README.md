# SRM Deploy

This directory contains CDK code constructs that will be called and assembled by higher level CDK Stack such as `lib/workload/orcabus-stateless-stack.ts`.

You may have multi-level directory structure under this folder as see fit to arrange your CDK constructs.

However. Collectively, all CDK constructs created under this deploy directory will form as **one deployable component unit** for the higher level CDK Stack. Hence, just single `component.ts` file might be sufficed if your app deployment is a simpler CDK deployment construction.
