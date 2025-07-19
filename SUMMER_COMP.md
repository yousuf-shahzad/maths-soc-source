# In-Depth Guide: Extending Maths Society Web App for a Multi-School Summer Competition

This guide provides a comprehensive, step-by-step plan for adapting your web application to support a regional summer competition spanning multiple schools.

---

## 1. Requirements Analysis

### 1.1 Stakeholder Questions
- How many schools will participate? Will they be pre-registered or self-registering?
- Will students have existing accounts, or will all users be new?
- Do you want to maintain “regular” school-year data entirely separately from summer data?
- Will the competition have its own set of challenges or reuse existing ones?
- What reporting and leaderboard views are required (per school, per user, per competition)?
- What are the security/privacy expectations for inter-school competition?

**Action:** Meet with stakeholders and record requirements for school onboarding, registration, and reporting.

---

## 2. Database Design & Migration

### 2.1 Add School Model

```python
class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    address = db.Column(db.String(255))
    # Optional: school_code for invite-only or email domain validation
    school_code = db.Column(db.String(20), unique=True, nullable=True)
    # Optional: contact_email, phone, etc.
```

### 2.2 Update User Model

```python
class User(db.Model):
    ...
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    school = db.relationship('School', backref='users')
```

- Make `school_id` required if all users must belong to a school.
- Consider enforcing email domain matching (e.g. `@school.edu`) if appropriate.

### 2.3 Add Competition Model

```python
class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
```

### 2.4 Relate Challenges, Submissions, Leaderboard to Competitions

- Add `competition_id` to `Challenge`, `AnswerSubmission`, and/or `LeaderboardEntry` (nullable for regular challenges).

```python
class Challenge(db.Model):
    ...
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=True)
    competition = db.relationship('Competition', backref='challenges')
```

- In `AnswerSubmission` and `LeaderboardEntry`, similarly add `competition_id`.

### 2.5 Migration

- Write Alembic migration scripts to add new tables and columns.
- Back up your database before applying migrations.
- Test migrations on a staging environment.

---

## 3. Registration Flow Changes

### 3.1 School Selection/Input

- **Admin-only:** Pre-populate schools and offer a dropdown on registration.
- **Self-service:** Allow users to request new schools (with approval), or allow free text.
- Optionally, require school-specific invite codes or email validation.

### 3.2 Registration Form

- Add a “School” field (dropdown or search) to registration.
- For summer competition, add a toggle or mode that registers users for the competition.

### 3.3 Registration Logic

- On registration:
  - Assign `school_id` to user.
  - (Optional) Assign `competition_id` if the user is registering specifically for summer competition.
  - Prevent duplicate users by name + year + school.

### 3.4 Admin Management

- Admin interface to add/edit schools and competitions.
- Optionally, allow each school to have its own admin.

---

## 4. Competition Lifecycle

### 4.1 Competition Creation

- Admin creates a new `Competition` in the admin interface.
- Define start/end, description, and (optionally) which schools are participating.

### 4.2 Challenge Assignment

- Admin assigns challenges to the competition.
- Challenges can be exclusive to the competition or shared.

### 4.3 Competition “Mode” UI

- Add banners and a dedicated landing page for the summer competition.
- Clearly separate summer competition leaderboards, challenges, and results from regular content.
- Optionally, hide regular content for competition users.

---

## 5. Leaderboards and Reporting

### 5.1 School Leaderboard

- Group and sum scores by `user.school_id` for the competition:
  - “Total School Score” = sum of all student scores from that school.
  - Display school rankings.

### 5.2 Individual Leaderboard

- Filter users by `competition_id`.
- Rank all students, with school affiliation shown.

### 5.3 Per-School Admin/Teacher View

- Allow each school’s admin/teacher to view their students’ progress and standings.
- Optionally, allow them to download CSV reports.

---

## 6. Security & Data Integrity

- Enforce unique users per school + year.
- Validate school on registration (invite code, email domain, or admin approval).
- Prevent “school hopping” (users should not be able to switch schools after registration).
- Limit data exposure: users should only see relevant competition/school data.

---

## 7. Testing

- Write new unit and integration tests for:
  - School registration and validation.
  - Competition participation.
  - Leaderboards grouped by school and competition.
  - Access control (school admins, competition admins, regular users).

---

## 8. Rollout & Operations

### 8.1 Staging

- Deploy all changes to a staging environment with test data.
- Simulate registration and competition flow.

### 8.2 Documentation

- Create onboarding documentation for:
  - School admins/teachers
  - Students/parents

### 8.3 Support

- Set up a support email or Discord/Slack for real-time help during competition.
- Monitor logs for suspicious activity, errors, or abuse.

### 8.4 Go-Live

- Announce competition and open registration.
- Monitor and support throughout competition window.

---

## 9. Post-Competition

- Archive results (export to CSV, PDF, or database snapshot).
- Optionally, “lock” competition data to prevent late submissions.
- Gather feedback from all stakeholders for future improvements.

---

## Example: Migration Command

```bash
# After updating models.py
flask db migrate -m "Add school and competition models"
flask db upgrade
```

## Example: School-Filtered Leaderboard SQL

```sql
SELECT school.name, SUM(leaderboard_entry.score) as total_score
FROM leaderboard_entry
JOIN user ON leaderboard_entry.user_id = user.id
JOIN school ON user.school_id = school.id
WHERE leaderboard_entry.competition_id = ?
GROUP BY school.name
ORDER BY total_score DESC;
```

---

## Appendix: Optional Advanced Features

- **Invite Codes:** Pre-generate codes per school, required at registration.
- **Teacher/Admin Roles:** Assign teachers as school admins for local support.
- **Bulk Student Upload:** Allow schools to upload CSVs of students.
- **Email Domain Verification:** Only allow emails from known school domains.

---

## References

- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [OWASP Flask Security Guide](https://cheatsheetseries.owasp.org/cheatsheets/Flask_Security_Cheat_Sheet.html)
- [Flask User Management Example](https://flask-user.readthedocs.io/en/latest/)

---

**For code examples, migration scripts, or implementation help for any step above, just ask!**