Had experimented with 3 open source solutions before architecting this solution. This brings the best of all worlds.

In the upcoming sections, as I cannot reveal the specific names of the solutions evaluated, I will use the aliases in the following table.
Name	Description
Solution A	The original deep research solution
Solution B	Another deep research solution that uses a fine-tuned model that is trained for deep research tool calling behaviour. The size of the base model is ~30 billion parameters
Solution C	Yet another deep research solution that uses a fine-tuned model trained for deep research tool calling behaviour, but uses a much smaller base model (~8 billion parameters). A newer solution than Solution A and B.

In a later section, I will detail on my original solution that works on a 4 billion parameter model with better results than solution C.