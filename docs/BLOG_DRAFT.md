# A test stand I can break on purpose

Unpublished prospective draft. Implementation and results are pending.


A machine that works once is satisfying. A machine that can explain why it stopped working is considerably more useful.

I like the part of engineering where software has to make sense of something physical. A sensor takes a measurement, some code decides what it means, and eventually a motor or valve does something. Each individual step can look straightforward. The timing between them is where things get interesting.

For this project, I want to build a small simulated test stand called AbyssBench. It has a pump, a valve, two pressure readings, and a flow reading. That is enough machinery to create some fairly annoying problems without filling my house with plumbing.

The question I want to explore is what happens when a reasonable-looking input stops being trustworthy. Suppose a pressure reading arrives right now, but the measurement was taken half a second ago. Suppose the connection drops while the pump is running and then comes back. Suppose the software correctly asks a valve to open, but the valve has decided to pursue other interests.

These are different failures, and I want the test software to preserve the difference. A command being issued is not evidence that the physical action occurred. A fresh network packet is not necessarily a fresh measurement. Reconnecting does not mean a machine should resume whatever it was doing before.

A simulator gives me a way to replay these situations exactly. I can freeze a sensor at a particular millisecond, compare two controller versions, and check the resulting sequence against a separate set of rules. The physics will be intentionally simple. The claim I care about is whether the controller follows its stated behavior under known faults.

That also makes this a useful experiment in agent-assisted software development. I can ask an agent to implement or repair the controller, then give it feedback from tests whose expectations it does not get to rewrite. I am particularly interested in the repairs that seem sensible until the next failure appears. Those are usually where the system's assumptions become visible.

I want the eventual demonstration to include a healthy run, a failure, and a repair, with enough evidence that someone else can reproduce all three. If the result is mostly a list of places where my original requirements were vague, I would still consider that useful. Finding an ambiguity while the pump is imaginary seems like a good deal.
