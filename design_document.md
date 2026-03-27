# I/O Function Guessing Bot – Design Specification

This document describes the behaviour, data structures, and flow of the Discord bot. It is intended as a guide for implementation, focusing on logic rather than code.

---

## 1. Game Overview

- A **game** is a session in a Discord channel, consisting of multiple rounds.
- **Recruitment**: After `-create`, players have a limited time to join with `-join`. If not enough join, the game is cancelled.
- **Rounds**: Each round, a different player from the participant list is the **creator**. The creator chooses a secret function.
- **Participants** (all except current creator) interact with the bot via DM:
  - **Query** → `f(x)` (or `f(x,y)`) → get output, lose potential.
  - **Guess** → `-guess f(3)=9` → guess an output; if correct, no penalty; if wrong, lose double penalty.
  - **Submit** → `-submit x**2` → submit a formula; if correct, solved and earn potential; if wrong, lose double penalty.
- Round ends after time limit or when all participants are out of potential or solved.
- **Scoring**: Solvers earn remaining potential; creator earns points based on % solved (target 50%).
- After all participants have been creator once, game ends with a leaderboard.

---

## 2. Game Rules

### 2.1 Recruitment Phase
- `-create [max_queries]` starts a game (max_queries defaults to 20).
- Recruitment lasts 30 seconds; players join with `-join`.
- If fewer than 2 players join (including creator), game is cancelled.

### 2.2 Round Structure
- Participants are ordered: creator of game first, then join order.
- Each round, the next person in the list becomes creator (round‑robin).
- Creator DMs a valid function expression (e.g., `x**2`, `x*y`).
- After the creator submits, round starts with a 90‑second timer.
- Participants DM the bot to interact.

### 2.3 Interaction Types (DM)
- **Query**: `f(x)` or `f(x,y)` → bot replies with result and deducts `penalty` from potential (if not solved).
- **Guess**: `-guess f(3)=9` → bot checks output; if correct, reply *"Correct guess!"* and no penalty; if wrong, reply *"Incorrect – correct output is Y"* and deduct `2*penalty`.
- **Submit**: `-submit <expression>` → bot tests expression on random points; if matches, marks solved, awards remaining potential, announces in channel; if wrong, deduct `2*penalty`.

### 2.4 Round End Conditions
- Timer reaches 90 seconds, OR
- All participants have potential ≤ 0 or have solved, OR
- A participant solves (submits correctly) – round ends immediately.

### 2.5 Scoring
- **Solver**: receives their remaining potential (0–1000) added to total score.
- **Creator**: receives `max(0, 1000 - 20 * |50 - p|)` points, where `p = 100 * (solved participants / total participants)` (0 if no participants).
- Scores are cumulative across rounds.

### 2.6 Game End
- After each participant has been creator once, game ends.
- Final scores announced; global leaderboard updated.

---

## 3. Technical Design

### 3.1 Data Structures (in memory)
- `Game` – holds per‑game state: channel, participants list, current round index, recruitment timer, list of `Round` objects.
- `Round` – holds for a single round: creator ID, max_queries, penalty, secret expression, start time, timeout task, map of `PlayerRoundState` (user ID -> potential, solved flag).
- `GamePlayer` – overall participant: user ID, total score.
- Global dictionaries: `games` (channel -> Game), `total_scores` (user ID -> total points), `pending_creators` (user ID -> (channel, round index)) to link DM function submissions.

### 3.2 Persistence
- Scores should be stored in SQLite to survive bot restarts. Table `scores` with user_id and total_score.

### 3.3 Evaluation
- Use `numexpr` to evaluate expressions safely.
- For `-submit`, test with 5 integer and 5 float random points within domain (e.g., 1‑20 for single‑var, 1‑10 for two‑var). Compare with tolerance 1e‑6.
- For `-guess`, compute exact output and compare with tolerance.

### 3.4 Timers
- Use `asyncio.create_task` for recruitment and round timeouts; cancel when not needed.

### 3.5 Command Cooldowns (optional)
- Rate‑limit `-join` and interactions to prevent spam.

---

## 4. Game Flow (Step‑by‑Step)

### 4.1 Starting a Game
- User in channel: `-create [max_queries]`
- Bot checks no active game in channel.
- Creates `Game` object, sets `current_round_index = -1`, starts recruitment timer (30s).
- Announces: *“Game created by @user! Use `-join` to join. 30 seconds.”*

### 4.2 Joining
- During recruitment, users send `-join` in channel.
- Bot adds them to `game.players` (if not already).
- Announce in channel: *“@user has joined!”*

### 4.3 Recruitment End
- After 30s, if `len(game.players) < 2`, cancel game.
- Else, build `participant_list`: creator of game first, then others in join order.
- Set `current_round_index = 0` and start first round.

### 4.4 Starting a Round
- Get next creator from `participant_list`.
- Create `Round` object with that creator, `max_queries` (from game), penalty = 1000 / max_queries.
- DM the creator: *“Please DM me the function expression (e.g., `x**2`).”*
- Store `pending_creators[creator.id] = (channel.id, round_index)`.

### 4.5 Creator Submits Function (DM)
- Bot receives DM from creator; check pending.
- Validate expression (must evaluate for test inputs).
- If valid, store in round, set `start_time`, schedule round timeout.
- Populate `round.players` with all participants except creator (initial potential = 1000).
- Announce in channel: *“Round X started! Creator: @creator. Max queries: Y, penalty = Z. DM queries/guesses/submits. 90 seconds.”*

### 4.6 DM Interactions (for participants)
- Bot receives DM; if user is in active round (and not creator), parse command:
  - **Query**: parse `f(x)` or `f(x,y)`, evaluate, apply penalty, reply.
  - **Guess**: parse `-guess f(x)=value`, compare, apply double penalty if wrong, reply.
  - **Submit**: parse `-submit expr`, test on random points, if correct → mark solved, award points, announce in channel, end round; if wrong → apply double penalty, reply.
- After each action, check round end condition.

### 4.7 Round End
- If round ends (timeout, all out, or solved), cancel timer.
- Compute: solved participants count, total participants (excluding creator).
- Creator points formula: if total participants > 0, `maker_points = max(0, 1000 - 20 * abs(50 - 100*solved/total))`.
- Add maker points to creator’s total score.
- Add each solver’s remaining potential to their total score.
- Announce round results.
- Move to next round if any, else end game.

### 4.8 Game End
- After all participants have been creator, announce final scores.
- Update global `total_scores` with each participant’s total.
- Remove game from `games`.

---

## 5. Command Specifications

- **`-create [max_queries]`** – starts a game with given max queries (default 20). Only if no active game in channel.
- **`-join`** – joins the current recruitment in that channel.
- **`-status`** – shows current game/round status (optional).
- **`-leaderboard [top]`** – shows global leaderboard (default top 10).
- **`-force_end`** – admin command to end current game early.

---

## 6. DM Interaction Patterns

- **Query**: must match `^f\((-?\d+(?:\.\d+)?)\)$` or `^f\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)$`.
- **Guess**: must match `^-guess f\((-?\d+(?:\.\d+)?)\)\s*=\s*(-?\d+(?:\.\d+)?)$` (extend to two‑var if needed).
- **Submit**: must match `^-submit\s+(.+)`.

All DM responses should include the user’s remaining potential (if relevant) and a clear message.

---

## 7. Evaluation & Scoring Details

- **Penalty per query** = `1000 / max_queries` (floating point).
- Double penalty for wrong guesses/submissions.
- Potential never goes below 0.
- Random test points for submission:
  - Single‑var: 5 integers in [1,20], 5 floats in [1,20].
  - Two‑var: 5 integer pairs in [1,10], 5 float pairs in [1,10].
- Tolerance = 1e‑6.

---

## 8. Edge Cases & Considerations

- **Invalid inputs**: If function is not defined for a query (e.g., division by zero), respond with “Error” and do not deduct penalty.
- **Creator queries**: The creator may query their own function (for testing); these queries do not affect potential or scores.
- **Simultaneous submissions**: If two players submit at the same time, the first to be processed (by the bot) wins; the second will see that the round has ended.
- **Timeouts**: Use `asyncio.create_task`; cancel on round end.
- **Persistence**: Load global scores from SQLite on startup; save after each game.
- **Security**: The secret function expression is stored only in memory; never exposed. `numexpr` is used for evaluation; it does not allow arbitrary code execution.

---

## 9. Implementation Plan (Suggested Order)

1. **Set up bot framework** – create cog, basic commands, DM handling.
2. **Implement data structures** – define classes for Game, Round, Player states.
3. **Implement `-create` and recruitment** – timer, join, cancellation.
4. **Implement function submission and validation** – DM handling, `numexpr` evaluation.
5. **Implement query handling** – regex, evaluation, potential update.
6. **Implement guess handling** – regex, comparison, penalty.
7. **Implement submit handling** – random testing, correct/incorrect logic.
8. **Implement round end and scoring** – calculation, announcements, next round.
9. **Implement game end and leaderboard** – final scores, persistence.
10. **Add admin commands, status command, error handling.**
