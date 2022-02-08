# Tian's x Robert's notes: 

Slide 8: put the text into different colors, and say red text and blue text;
make the red box to be slightly bigger, and line weight to be thick. 

openning slide: 

slide 2:
- fundamental questions ? different word choice: important/basic/??
- maybe have an animina tion that shows up the two steps we are taking in the
  talk, by showing them one by one in boxes
.

slide 3:
- mention GPU acceleration: it helps, but training still takes time
- multiple seessions - needs to be done repeatively 

slide 4:
 - this is used by tensor flow
- the bullets texts are too small, also, we do not need to use bullets 
- each workers do it independently from each other, essentially the
  asynchronous 

slide 5
- transient servers are not the solution... if they are already the solutions,
  what are we doing here? Call them a "promising solution".

slide 6
- the last point about accuracy drop? where does it come from? 

slide 8
- Rephrase observation: "Transient servers offer the same performance as
  on-demand servers, sans revocation"
- you did not really explain what top 1 accuracy is, but just converged
  accuracy itself. maybe also menntioning the 64K steps here 
- don't apologize during the talk, just pause and continue...
 
slide 9
- it important to mention the drop in accuracy is from distributed training, but not from
using transient server 
- maybe spent too much time in the first row, since it is essentially the same
  as last slide. 
- 
slide 10 
- also, just immediately show only the 2 revocations part 

slide 11
- maybe don't say "scaling up or out". just say, more powerful GPU servers
  etc

slide 12
- need to rephrase the observation 4



Slide 14 
- the first opportunity that we identity 
- too much detail about the checkpointing, get to the point quicker, i.e., "if
  the chief worker fails, then the training doesn't finish"

Slide 15
- what part of the figure demonstrates the "mass revocations?"


Slide 16
- start with high-level definition of "dynamic training configurations"
- the figure is still blurring 
- as we can see, as we dyanically adjusting the learning rate as we increase
  the size of cluster, we mitigate the accuracy impact 

slide 17
- availabiltiy of region A going down, just say, we will not be able to get new
  transient servers from region A when we need them. 
- the numbers in the parathesis represents the number of workers from the
  designated regions 
- " compared to: all ... " need a space, and say (4,0,0), and change all the
  configurations to match this format.

slide 19
- just say "our large scale empirical studies", not "some large scale studies" 

Total time is 29 mins.  

- don't mirror the screen, just use projector as a secondary screen.  

practice, practice, practice 
