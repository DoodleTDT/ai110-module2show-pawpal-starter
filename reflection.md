# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
The user should be able to identify themselves and the pet(s) they have. The user should be able to add/delete pet tasks from their list, ordering them by priority. The user can also pick a time frame they prefer for the task, as well as how long it may take. The assistant should be able to read that list of tasks and create a plan for the user to follow based on a 24 hour clock. The assistant should consider the priorities of each task. The assitant should also consider any constraints the user may have, including sleep schedule and outside events. The assistant should explain the plan to the user.

- What classes did you include, and what responsibilities did you assign to each?
User: creates tasks for the assistant to read, enters owner and pet information into the system, adds time preferences to tasks, adds priority ratings to tasks, adds outside events/times that restrict them

Pet: Stores information about any pets the user adds. Should make a new 'pet' object for each pet the user owns.

Task: Stores the tasks that the user adds. Lists them by priority and time preference. Should include pet related tasks and non-pet tasks as categories (requirements and constraints). Should store which pet(s) the task is for.

Schedule: Where the assistant stores the daily plan for the user to view. Should only work from 12 am to 11:59 pm the same day.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
The original design did not consider dependencies to tasks (ex. Eating breakfast should come before washing the dog). I made the change for the user to be able to mark tasks as dependent on others. There are now methods so the schedule can read these dependencies and consider them for the daily schedule. The dependent tasks are now considered before the priority scale, and any deleted tasks will also delete any connected dependencies.

Also added a method that stores the saved daily schedule, so the user can come back to the program and view it. No history outside of the daily schedule will be stored at this time.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
The main constraint the scheduler has is the owner's sleep schedule. No tasks can be placed during that time. There are also fixed tasks that the scheduler cannot move or edit over. Daily tasks need to happen every day, and weekly tasks happen at least once. They cannot be left out. If a task requires another task to finish it (prerequisite), then that task must be placed before the other. After that, if a task has a preferred start time, then the scheduler will try to give it that spot. However, if two tasks have the same preferred start time, the one with the highest priority rating will take the spot first. And if their are any leftover tasks with no preferred time, then they will be placed depending on the plan. Plan A focuses on priority, and Plan B focuses on the shortest task.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
One tradeoff is that the scheduler does not recognize two tasks with the same category or type as something that can be done together. For example, if their are two tasks, one to feed a cat and one to feed a dog, the scheduler will seperate the two as they are. I considered fixing that for certain tasks, but since the scheduler already allows for multiple pets to be added to a task, it is redundant.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
The AI was most helpful while coming up with the design for the code. While I had an idea of what classes and methods those classes needed, Claude kept suggesting possible functions or holes in the code that I hadn't considered. This made the immplementation of logic much smoother, as I wasn't still stuck on what needed to happen.


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
As nice as it was for the AI to help with designing a plan, it was also the most error filled. Claude will add new classes that you didn't want, even if you specify to only use a certain amount. And sometimes it was user error, as Claude will fill in gaps I may have left in the prompt. The main thing was to continue to review over what it did and correct my parameters from there.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
Tests made were surrounding the priority hill of the schedules. Testing if priority level beats the preferred time the user added. Testing which tasks will be added first if they all had the same priorty levels. If none of them had a preferred time. Would a owner task or appointment push everything back, or would the scheduler move it around with the others. The main tests were to make sure the schedules wouldn't shuffle anything out of place.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
If I had more time, I'd test how the schedule deals with no time left to add to the list. While I did have this tested once, that was before I allowed the schedule to hold more than one day at a time. Multiple days allows tasks to be distibuted better, which means I need way more tasks to really fill up the days.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I'm most satisfied with the implementation of two different schedules the user can choose between. Especially since some like schedules done in different ways.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would to improve the wording used for some of the scheduling UI. It's very plain and could be more user friendly. Color coding or marking the different tasks with emojis would also be something I'd add. And if the user has enough tasks, I'd like to make a possible third schedule they could choose from. I don't know what it sort by, but it could be nice.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
Having a good baseline for what the program you're creating is the most important thing I learned. And not just the first thing you create can be the plan you go for. The first draft is never the final one with AI, no matter fast it works.
