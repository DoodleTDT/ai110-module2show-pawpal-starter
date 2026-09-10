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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
