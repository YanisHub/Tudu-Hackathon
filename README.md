# TuDu – Product Vision

## Objective

TuDu is a digital marketplace that enables students to invite qualified collaborators to help with school projects. By matching learners who need support on complex or time‑consuming assignments with peers who have the right skills, TuDu streamlines project management and fosters teamwork.

---

## Bear in mind

What will set you apart?

* **Inventive features that transcend the brief**
* **Clean, modern UX / UI that feels premium out of the box**
* **Bulletproof architecture, thoughtful documentation and scalable tech stack**
* **Relentless polish under extreme time pressure (14 days, tick‑tock)**
* **Team size up to 2 (full‑stack dev, UI/UX). You may participate alone; this will be taken into account when determining the leaderboard**

---

## Key Features

### Authentication & Onboarding

* Secure sign‑up and login system + social authentication (Google)
* Upon registration, users are prompted to complete their profile (name, university, skills **with proof**, verification method — e.g. LinkedIn URL, diploma scan, certificate PDF): **Onboarding Stage**
* Any skill added later must also include at least one supporting proof document or link; unverified skills remain hidden from search until proof is supplied.

### User Interface

An intuitive interface with navigation between:

* **My Projects**: projects created by the user.
* **Work to Do**: projects the user has accepted.
* **Marketplace**: list of open projects available for application.
* **Profile**: personal info, skills, **ratings**, history, etc.

The frontend's intuitiveness and quality will be key points of attention for us.

### Reputation, Ratings & Skill Verification

* **Two‑way Rating System** – After each project, both the client and the collaborator leave a 1‑to‑5 star rating plus an optional tagged comment (quality, communication, timeliness). Overall and skill‑specific ratings are shown on user profiles and influence search ranking.
* **Evidence‑backed Skills** – Every competence must be justified with a verifiable proof (e.g. LinkedIn profile, diploma, GitHub repo). Proofs are stored and displayed as badges (\*Verified\* / \*Pending\*). Skills with no accepted proof cannot be displayed publicly nor used in search filters.
* **Reputation Guardrails** – Accounts falling below a 3‑star average across their last 5 projects are flagged for review, temporarily lowering their marketplace visibility until issues are resolved.

---

## Technical Features

### Project Creation & Management

Users can create a project (e.g. maths homework).

Once published, the project is listed in the marketplace.
The creator can monitor its progress through the **My Orders** page.

---

### Project Lifecycle

Each project follows a standardized 6‑stage lifecycle:

1. **Draft**: project is being written.
2. **Open for Applications**: visible on the marketplace.
3. **In Progress**: a provider has been selected and the payment is held in escrow.
4. **In Review**: project has been delivered and is awaiting approval and rating.
5. **Completed / Cancelled**: project is either finalized or interrupted. Ratings are finalized at this step.

---

### Selection Process & Secure Payment (using Stripe or any other alternatives)

* Interested users can apply to open projects.
* The project creator selects one provider among the applicants. Applications display each candidate’s rating average, number of completed projects, and verified skill badges.
* Upon selection, client funds are held in **escrow**.
* The project status changes to **In Progress**, and a dedicated **chat** is activated, allowing the owner and the selected applicant to further discuss the project.

---

### Integrated Messaging

* Real‑time chat system between the project owner and the provider.
* Centralized exchange of messages and files.

---

### Delivery, Validation & Payment

* Once the delivery is made, the client may request a revision or approve the project.
* Upon approval, funds are released to the provider **and both parties are prompted to leave a rating & review**.
* In case of disputes, a support system may be implemented later.

---

### Data Integrity & Verification Services *(new)*

* Integration with external APIs (LinkedIn, GitHub, university registries) to automatically fetch and validate proof-of‑skill documents wherever possible.
* Manual moderation dashboard for edge cases where automated verification fails.

---

## KPIs & Success Metrics

* **Average project rating** and distribution across collaborators.
* **Percentage of skills with verified proof** vs total declared skills.
* **Dispute rate** (number of disputes per 100 completed projects).
* **Average project completion time**.

---

## Future Enhancements

* Gamification (achievement badges for milestones such as \*100 5‑star projects\*).
* AI‑powered skill recommendations based on verified accomplishments.
* Reputation insurance to cover project cancellation scenarios.

---

## Tech Stack Suggestions

* **Frontend**: React / Next.js + Tailwind CSS (or similar), WebSockets for real‑time chat.
* **Backend**: Node.js with TypeScript or Python (FastAPI). JWT‑based auth.
* **Database**: PostgreSQL + Prisma / SQLAlchemy.
* **File Storage**: AWS S3 or similar for proof documents.
* **Payments**: Stripe Connect with escrow logic.
* **CI/CD & Ops**: Docker, GitHub Actions, scalable cloud hosting (e.g. Render, AWS ECS).

---

## Timeline & Team

14 days, maximum two people. Maintain code quality, documentation, and testing discipline; treat this project like production code.

