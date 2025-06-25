# TUDU – Product Vision

## Objective

TUDU is a digital platform designed to let students delegate their university projects to other qualified students or freelancers, in exchange for payment.
This marketplace simplifies the management of complex and time-consuming assignments by connecting those who want to outsource their projects with those capable of completing them efficiently.

---
## Bear in mind

What will set you apart?
* **Inventive features that transcend the brief**
* **Clean, modern UX / UI that feels premium out of the box**
* **Bulletproof architecture and thoughtful documentation**
* **Relentless polish under extreme time pressure (7 days, tick-tock)**
  
---
## Key Features

### Authentication & Onboarding

* Secure sign-up and login system + social authentication (Google)
* Upon registration, users are prompted to complete their profile (name, university, skills, verification method — e.g. LinkedIn): Onboarding Stage

### User Interface

An intuitive interface with navigation between:

* **My Orders**: projects created by the user.
* **Work to Do**: projects the user has accepted.
* **Marketplace**: list of open projects available for application.
* **Profile**: personal info, skills, history, etc.

The frontend's intuitiveness and quality will be key points of attention for us.

---

## Technical Features

### Project Creation & Management

Users can create a project (e.g. maths homework).

Once published, the project is listed in the marketplace.
The creator can monitor its progress through the **My Orders** page.

---

### Project Lifecycle

Each project follows a standardized 6-stage lifecycle:

1. **Draft**: project is being written.
2. **Open for Applications**: visible on the marketplace.
3. **In Progress**: a provider has been selected and the payment is held in escrow.
4. **In Review**: project has been delivered and is awaiting approval.
5. **Completed / Cancelled**: project is either finalized or interrupted.

---

### Selection Process & Secure Payment (using Stripe or any other alternatives)

* Interested users can apply to open projects.
* The project creator selects one provider among the applicants.
* Upon selection, client funds are held in **escrow**.
* The project status changes to **In Progress**, and a dedicated **chat** is activated, allowing the owner and the selected applicant to further discuss the project.

---

### Integrated Messaging

* Real-time chat system between the project owner and the provider.
* Centralized exchange of messages and files.

---

### Delivery, Validation & Payment

* Once the delivery is made, the client may request a revision or approve the project.
* Upon approval, funds are released to the provider.
* In case of disputes, a support system may be implemented later.

---

To give you the big picture, I’ve provided the first version of a Python backend. Bear in mind that you can use the tech stack you want, but the most scalable and up-to-date technologies will be preferred.
