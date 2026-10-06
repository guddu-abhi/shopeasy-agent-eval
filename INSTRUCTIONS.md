Welcome to this technical test!

Below is a description of what the test is about and what we'll need from you.

### The situation

You are being onboarded in an AI agent prototype project.  
So far it has been driven by two devs, which were able to get something up and running, but they are dissatisfied with the agent's performance.  
They weren't exactly clear on how to measure said performance, and they are both out of office this week. Bummer!  

Regardless, you are being asked to improve the agent's performance.  
At least you have a set of eval queries and a dataset to work with.

### What you must do

1. Establish what performance should be at this stage of the project.
2. Find ways to measure and improve it.

Your only constraint are:

- you cannot *remove* any of the existing evaluation examples (feel free to add any)
- your solution must make use of an LLM-based agent built using LangGraph that leverages tools to answer user queries
- your solution must maintain the same underlying LLM model; improvements should come from elsewhere than just using a smarter model

### Deliverables

1. Your fork of this current repo
2. A new report file (Markdown, Jupyter Notebook, PDF, as you prefer) that:
    - explains and justifies your approach
    - presents your results
    - prioritizes likely next steps if you were to spend more time on this

Your overall objective is to convince us that your version is indeed an improvement over the current one, and that the way you got there makes sense.

### A few tips

- The report is the main deliverable here. It lets us see how you think about the problem, which is more valuable to us than the implementation itself. The code must run, but don't spend too much time polishing it.
- Quality/performance is currently undefined. You are expected to fill this gap.
- The repo is intentionally very bare bones. Feel free to add whatever would help achieve the objective: dependencies, tools, modules, etc.
- Avoid providing a laundry list of all possible improvements from there; provide clear direction for next steps and take the time to explain your recommendations.
- We already lazily asked an AI coding CLI agent to solve the problem and were disappointed with the results. We're looking for people who can do better than that!
