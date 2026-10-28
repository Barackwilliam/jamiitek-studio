# Usability Test Plan (TASK-107)

This plan is for testing JamiiTek AI Marketing Studio with real small-business owners. It costs nothing beyond the participants' time; offer airtime or a free poster for their business as thanks if you can.

## 1. Goals

1. Can a business owner go from a new account to an approved script and a downloaded poster or video without help?
2. Is the Kiswahili interface natural and clear? Which words confuse people?
3. Do people understand why information must be confirmed, and why claims are highlighted?
4. Where do people hesitate, give up or make mistakes?

## 2. Participants

- 5 participants are enough to find most problems; run a second round of 5 after fixes.
- Mix: at least 3 who prefer Kiswahili; at least 2 with a website and 2 without; at least 3 using a phone.
- Examples: a caterer, a clothing shop, a tour operator, a salon, a hardware shop.
- Ask for consent to take notes (and screen recording only if they agree). Do not record their passwords or customers' data.

## 3. Setup

- Run the application on a laptop on the same Wi‑Fi, or on a test deployment. Start the worker (`python manage.py run_worker`) and make sure AI writing and FFmpeg work before the session.
- Prepare a fresh account for each participant, or let them sign up as task 1.
- Have 3–5 photos of their business on their phone, or sample photos ready.

## 4. Tasks (read aloud, do not demonstrate)

1. "Create an account and a project for your business."
2. "Let the system read your website" (or "describe your business" if no website).
3. "Check what was found. Correct anything wrong and add your phone number."
4. "Create content to get more orders on WhatsApp Status, in Kiswahili."
5. "Choose a concept you like, get a script, and change one sentence."
6. "Approve the script." (Note whether they read the highlighted claims.)
7. "Make a poster with one of your photos and download it."
8. "Make a short video preview."
9. "Switch the screen to English and back." (Only if time allows.)

## 5. What to observe

For each task, record: completed without help / with a hint / not completed; time taken; words they asked about; where they hesitated; anything they said was wrong about their business.

Ask them to think aloud. If they are stuck for more than 2 minutes, give one hint and note it.

## 6. Questions after the session

1. What was easiest? What was hardest?
2. Which words in Kiswahili sounded strange or unclear? What would you say instead?
3. Would you post the poster or video you made? Why or why not?
4. Did you trust that the content was true about your business?
5. On a scale of 1–5, how likely would you be to use this again?

## 7. After each round

- List problems by how many participants hit them and how badly they were blocked.
- Fix problems that blocked 2 or more people first. Update `locale/sw/LC_MESSAGES/django.po` with better words.
- Record the round in `docs/PROJECT_STATUS.md` (date, number of participants, completion rate per task, main findings, changes made), and mark TASK-107 done after the second round.
