Measuring Progress Toward AGI - Cognitive Abilities
Design high-quality benchmarks that go beyond recall to evaluate how frontier models truly reason, act, and judge.

Measuring Progress Toward AGI - Cognitive Abilities

Join Hackathon
This competition requires identity verification
To submit to this competition, you'll need to verify your identity. Learn More

Verify now
Overview
Current AI models often succeed by exploiting familiar data or memorized patterns, making existing evaluations poor judges of how models truly think. This hackathon challenges you to bridge that gap. Your task is to create high-quality benchmarks with Kaggle’s Benchmarks to test true understanding. We are asking you to focus on the cognitive faculties highlighted in Google DeepMind’s paper— Measuring progress toward AGI: A cognitive framework. The five faculties and tracks to focus on are: learning, metacognition, attention, executive functions, and social cognition. Designing these rigorous standards will build detailed cognitive profiles of frontier models and reveal exactly how close we are to achieving Artificial General Intelligence (AGI).

Start

4 days ago
Close
a month to go
Description
Imagine a student who gets an A+ on a history test not because they understand the underlying events, but because they memorized the textbook. Current AI models can be similar: they display remarkable flashes of brilliance and crystallized knowledge, but often rely on surface-level patterns rather than fluid intelligence. This makes it difficult to distinguish when a model is truly solving a novel problem versus when it is simply recalling a scenario it has seen in its training data.

The core problem is that we lack an empirical framework to measure these limitations. We need evaluations that isolate specific cognitive abilities, resist shortcut solutions, and expose systematic failure modes. Without such benchmarks, progress toward human-level generality becomes difficult to interpret, comparisons between models become noisy, and important weaknesses remain hidden until deployment.

To move the field forward, we must look into the core cognitive faculties—the internal gears that determine how a system learns, monitors its own logic, and navigates nuance.

In this competition, hosted by Google DeepMind and Kaggle, we are inviting the Kaggle community to help solve this by building high-quality benchmarks designed to dig deeper than standard evaluations. Your goal is to create a Kaggle benchmark (with underlying tasks) using datasets that isolate specific cognitive abilities across five critical tracks: learning, metacognition, attention, executive functions, and social cognition. Using the new Kaggle Benchmarks platform, you will help the industry move away from broad, static scores and toward generating detailed cognitive profiles for frontier models.

A successful submission should answer a simple question: “What can this benchmark tell us about model behavior that we could not see before?”

This is your opportunity to contribute to the fast-growing field of AI research. By crowdsourcing novel benchmark ideas from researchers, practitioners, and domain experts, this hackathon aims to transform Artificial General Intelligence (AGI) from a subject of speculation into a grounded, measurable scientific endeavor.

If you have feedback on the Benchmarks product, please document it on this discussion forum thread, or join this Discord channel

Timeline
March 17, 2026 - Start Date.
April 16, 2026 - Final Submission Deadline.
April 17 - May 31, 2026 - Judging Period*
May 22, 2026 - Deadline to vote on other participants' benchmarks.
June 1, 2026 - Anticipated Results Announcement.
*Note - Judging period subject to change based on the number of submissions received

All deadlines are at 11:59 PM UTC on the corresponding day unless otherwise noted. The competition organizers reserve the right to update the contest timeline if they deem it necessary.

Submission Requirements
Note: Upon joining this hackathon, your Kaggle account will be provisioned with extra quota ($50/day, $500/month) to run the AI models for your benchmark. Read the Rules section 3.4.b to learn more.

A valid submission must contain the following:

Kaggle Writeup
[Mandatory] Kaggle Benchmark, as an attachment > “project links” > “Benchmark”
[Optional] Media Gallery
[Optional] Attached Public Notebook
Your final Submission must be made prior to the deadline. Any un-submitted or draft Writeups by the competition deadline will not be considered by the Judges.

To create a new Writeup, click on the "New Writeup" button here. After you have saved your Writeup, you should see a "Submit" button in the top right corner.

Note: If you attach a private Kaggle Resource to your public Kaggle Writeup, your private Resource will automatically be made public after the deadline.

1. Kaggle Writeup
   The Kaggle Writeup serves as your project report. This should include a title, subtitle, and a detailed analysis of your submission. You must select a Track for your Writeup in order to submit.

Your Writeup should not exceed 1,500 words. Submissions over this limit may be subject to penalty.

The below assets must be attached to the Writeup to be eligible.

a. Kaggle Benchmark [mandatory]
This is the most important part of your writeup submission. You must create a Kaggle Benchmark with underlying tasks — all of which should be authored by you — and link the benchmark in the writeup as a project link (see section D below for more details). The tasks and benchmark should all be set to private. After the submission deadline, all tasks and benchmarks are published publicly.

Kaggle Benchmarks is a product that lets you – the Kaggle community – build, run, and share your own custom benchmarks for evaluating AI models at no cost.

Powered by the kaggle-benchmarks SDK, you can now create your own AI evaluations (“tasks”) and put them together into a collection (“benchmark”).

For more helpful resources, see:

- Kaggle Benchmarks guide

- Getting started notebook

- YouTube tutorial

- Kaggle-benchmarks open source GitHub Repo & DeepWiki

- Benchmarks cookbook: Guide to advanced features and use cases

- Example tasks: Get inspired with a variety of pre-built tasks

b. Media Gallery [optional]
This is where you should attach any images and/or videos associated with your submission. A cover image is required to submit your Writeup.

c. Public Notebook [optional]
Your code should be submitted as a public notebook in the Project Files field. Your notebook should be publicly accessible and not require a login or paywall. If you use a private Kaggle Notebook, it will automatically be made public after the deadline.

d. Public Project Link [mandatory]
A URL to your benchmark. This allows judges to analyze your project firsthand. Under the section “Attachments”, click on “Add a link”. This will open a panel on the right, where you will be able to select your benchmark and add it to the project.

Evaluation
Minimum requirements
Target one primary domain (to keep the signal sharp),
Clearly state which capability is being isolated, and
Explain what new insight the benchmark reveals about model behavior within that domain.
Evaluation
Submissions are evaluated on the following criteria:

Criteria (Percentage) Description
Dataset quality & task construction
(50%) Is the data defensible?

- Verifiably correct answers (no ambiguity)
- Sufficient sample size to be statistically significant

Are the tasks and benchmark built well?

- Clean, readable code
- Input prompt and output verification are robust.
  Writeup quality
  (20%) Can the community use and learn from this? High quality writeups covering:
- Problem Statement: Which domains are you trying to solve and why
- Task & benchmark construction: How you’ve structured the code for the actual tasks and benchmark
- Dataset: its provenance, columns, and data types
- Technical details: Any additional details on how you implemented the benchmark or techniques
- Results, insights, and conclusions: How did the LLMs perform and what unique insights did you learn
- Organizational affiliations: Which organizations you might be affiliated with
- References & citations: Cite relevant work or papers that are similar or relevant to your submission.
  Discriminatory power
  (15%) Does the benchmark provide a meaningful signal?

We are looking for a gradient of performance. Can the benchmark significantly distinguish model performance?

A benchmark where everyone scores 0% is as useless as one where everyone scores 100%.
Community upvotes
(15%) How many upvotes the benchmark gets from other Kaggle users. Only benchmark votes will be counted, not Writeup votes.
Proposed Writeup template
Use the following structure and in 3 pages or less present your work.

### Project Name

### Your Team

### Problem Statement

### Task & benchmark construction

### Dataset

### Technical details

### Results, insights, and conclusions

### Organizational affiliations

### References & citations

Note: If you attach a private Kaggle Resource to your public Kaggle Writeup, your private Resource will automatically be made public after the deadline.
