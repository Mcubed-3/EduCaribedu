"""
EduCarib AI – Blog post data store.

Add new posts to the POSTS list. Most-recent post should be first.
Each post requires: slug, title, description, date, author,
read_time, category, and content (plain HTML string).
"""

from __future__ import annotations

POSTS: list[dict] = [
    {
        "slug": "curriculum-alignment-caribbean-teachers",
        "title": "What Is Curriculum Alignment and Why Does It Matter for Your Students?",
        "description": (
            "Curriculum alignment connects what you teach, how you teach it, and how you "
            "assess it. Here is why it matters for Caribbean classrooms and how to check "
            "whether your lessons are truly aligned."
        ),
        "date": "2025-04-14",
        "date_display": "14 April 2025",
        "author": "EduCarib AI Team",
        "read_time": "6 min read",
        "category": "Curriculum & Planning",
        "image_alt": "Teacher writing lesson objectives on a whiteboard",
        "content": """
<p>When a student fails a test on material you are certain you covered, the first question worth asking is not "Did they study?" — it is "Was my lesson actually aligned to the assessment?" This is the core idea behind <strong>curriculum alignment</strong>, and it is one of the most powerful levers a teacher has for improving student outcomes.</p>

<h2>What curriculum alignment actually means</h2>
<p>Curriculum alignment refers to the degree to which three elements work together:</p>
<ul>
  <li><strong>The intended curriculum</strong> – what the official syllabus or framework says students should learn</li>
  <li><strong>The taught curriculum</strong> – what actually happens in your classroom day to day</li>
  <li><strong>The assessed curriculum</strong> – what your tests, assignments, and projects measure</li>
</ul>
<p>When all three are in sync, students are taught exactly what they will be assessed on, and both are grounded in the national or regional standards. When they fall out of alignment — which happens more often than most teachers realise — students can work hard and still underperform, simply because what was taught and what was tested are not quite the same thing.</p>

<h2>Why it matters more in the Caribbean context</h2>
<p>Caribbean teachers face a specific challenge: many schools follow national or regional curriculum frameworks (such as those set by the Caribbean Examinations Council or Ministry of Education syllabuses), but lesson planning resources are often generic, imported, or out of date. This creates a gap between the official standards and what gets taught in practice.</p>
<p>Closing that gap is not just an academic exercise. Research consistently shows that students in systems with high curriculum alignment outperform peers in misaligned systems — even when teacher quality is held constant. For Caribbean students preparing for CXC, CSEC, or national assessments, alignment is not optional. It is the foundation.</p>

<h2>Three signs your lessons may not be aligned</h2>
<p><strong>1. Your objectives are vague.</strong> Phrases like "students will understand fractions" or "students will appreciate poetry" are not measurable. If you cannot write a test question that directly assesses your stated objective, the objective needs to be sharpened.</p>
<p><strong>2. Your activities do not match your objectives.</strong> If your objective asks students to <em>analyse</em> a poem but your activity only asks them to <em>read and summarise</em> it, there is a mismatch. The cognitive demand of the activity must match the cognitive demand of the objective.</p>
<p><strong>3. Your assessments test things you did not explicitly teach.</strong> This happens most often when teachers borrow test questions from external sources without checking them against their own lesson content.</p>

<h2>How to check your alignment quickly</h2>
<p>A simple three-column check works well. Take your lesson plan and list your learning objective in the first column, the main activity in the second, and your assessment question or task in the third. Read across each row and ask: do these three things ask for the same cognitive skill at the same level of difficulty? If not, something needs adjusting — usually the activity or the assessment.</p>
<p>Bloom's Taxonomy is a practical tool here. If your objective uses a verb like <em>evaluate</em> or <em>create</em>, your activity and assessment should demand that same level of thinking, not just <em>recall</em> or <em>describe</em>.</p>

<h2>How EduCarib AI helps</h2>
<p>EduCarib AI generates lesson plans that are built around the Caribbean curriculum framework from the start. Every objective is written using measurable Bloom's verbs, and the activities generated are matched to those objectives by design. This does not remove the need for teacher judgment — but it gives you a strong, aligned starting point that is much faster than building from scratch.</p>
<p>If you want to see what curriculum-aligned lesson planning looks like in practice, the <a href="/lesson-examples">lesson examples</a> page shows real outputs across multiple subjects and grade levels.</p>
""",
    },
    {
        "slug": "lesson-planning-mistakes-caribbean-teachers",
        "title": "5 Common Lesson Planning Mistakes Caribbean Teachers Make (And How to Fix Them)",
        "description": (
            "Even experienced teachers fall into the same planning traps. Here are five of the "
            "most common mistakes seen in Caribbean classrooms — and practical fixes for each one."
        ),
        "date": "2025-04-07",
        "date_display": "7 April 2025",
        "author": "EduCarib AI Team",
        "read_time": "7 min read",
        "category": "Teaching Tips",
        "image_alt": "Open lesson plan notebook on a teacher's desk",
        "content": """
<p>Lesson planning is one of the most time-consuming parts of teaching, and under pressure most teachers fall into familiar habits. The problem is that some of those habits quietly undermine what happens in the classroom. Here are five mistakes worth looking out for — and how to address each one.</p>

<h2>1. Writing objectives that cannot be measured</h2>
<p>The most common planning mistake is using vague language in learning objectives. "Students will understand the water cycle" sounds reasonable, but <em>understand</em> tells you nothing about what a student should be able to do at the end of the lesson.</p>
<p><strong>The fix:</strong> Replace vague verbs with observable ones. Instead of "understand," use "explain," "label," "sequence," or "compare" — verbs you can actually assess. Bloom's Taxonomy gives you a full list organised by cognitive level. A good objective sounds like: "Students will be able to sequence the four stages of the water cycle and explain what drives each transition."</p>

<h2>2. Activities that do not match the objective's cognitive level</h2>
<p>You set an objective at the analysis level, then spend the lesson on recall activities — copying notes, matching definitions, filling in blanks. Students complete the activities successfully but cannot answer the exam question, which requires them to actually analyse something. This mismatch is extremely common and rarely noticed until the assessment.</p>
<p><strong>The fix:</strong> Before finalising your plan, check that each activity demands the same level of thinking as the objective. If your objective uses <em>evaluate</em>, at least one activity should require students to make and defend a judgment — not just recall facts.</p>

<h2>3. No differentiation for mixed-ability classes</h2>
<p>Most Caribbean classrooms are mixed ability. A single lesson plan designed for one level will leave the weakest students lost and the strongest students bored. Yet many plans are written as if all students will respond identically to the same input.</p>
<p><strong>The fix:</strong> Build at least two tiers into your main activity — a supported version with scaffolding for students who need it (sentence starters, graphic organisers, worked examples) and an extended version for students who finish early. You do not need to write separate lesson plans; a two-tier activity within one plan is usually enough.</p>

<h2>4. Skipping the closure</h2>
<p>When time runs short, the first thing most teachers cut is the lesson closure. This is a significant loss. Closure — whether it is an exit ticket, a think-pair-share, or a one-sentence summary — is where learning consolidates. Without it, students leave with a loosely connected set of activities rather than a clear understanding of what they were supposed to learn.</p>
<p><strong>The fix:</strong> Protect five minutes at the end of every lesson for closure. Plan it in from the start, not as an afterthought. A simple prompt works: "Write one thing you learned today and one question you still have." This takes three minutes to complete and gives you instant formative data for the next lesson.</p>

<h2>5. Treating the lesson plan as a one-time document</h2>
<p>A lesson plan written once and never revisited is a missed opportunity. The most useful thing you can do with a lesson plan is annotate it after the lesson — what worked, what did not, where students struggled, what you would change. Most teachers do not do this because they are too busy, which means they repeat the same mistakes the next time they teach the topic.</p>
<p><strong>The fix:</strong> Keep one editable version of each lesson plan and add two or three notes directly after teaching it. This takes less than five minutes and turns your planning library into something genuinely useful over time. Digital tools make this easier — EduCarib AI lets you save and edit your generated lesson plans so you can build on them rather than starting from scratch each year.</p>

<h2>One underlying pattern</h2>
<p>Look back at all five mistakes and you will notice a common thread: they all involve a gap between intention and execution. The plan says one thing; the classroom does another. Closing those gaps, even partially, is what separates a lesson that merely occupies time from one that actually builds understanding.</p>
""",
    },
    {
        "slug": "how-to-write-learning-objectives-caribbean-teachers",
        "title": "How to Write Learning Objectives That Actually Work: A Caribbean Teacher's Guide",
        "description": (
            "Strong learning objectives are the foundation of every effective lesson. "
            "This guide explains Bloom's Taxonomy, shows you how to write measurable objectives, "
            "and gives you examples built for Caribbean classrooms."
        ),
        "date": "2025-03-31",
        "date_display": "31 March 2025",
        "author": "EduCarib AI Team",
        "read_time": "8 min read",
        "category": "Curriculum & Planning",
        "image_alt": "Bloom's Taxonomy pyramid diagram with coloured tiers",
        "content": """
<p>A learning objective is a single sentence that describes what a student will be able to do by the end of a lesson. That sounds simple. In practice, writing objectives that are clear, measurable, and pitched at the right cognitive level is one of the hardest skills in teaching — and one of the most consequential, because everything else in a lesson plan depends on it.</p>

<h2>Why most learning objectives fall short</h2>
<p>The two most common problems with learning objectives are vagueness and ambition mismatch.</p>
<p><strong>Vagueness</strong> looks like this: "Students will understand photosynthesis." The word <em>understand</em> is not measurable. Two teachers can read that objective and have completely different lessons in mind. One teacher's assessment might ask students to label a diagram; another's might ask them to explain why plants in low-light environments grow more slowly. Both lessons are teaching "understanding" — but they are not the same lesson.</p>
<p><strong>Ambition mismatch</strong> looks like this: writing an objective that demands high-level thinking ("Students will evaluate the impact of colonialism on Caribbean identity") for a 45-minute introductory lesson with Year 7 students who have never encountered the topic. The objective is not wrong — it may be the right destination — but it is not achievable in one lesson from a standing start.</p>

<h2>Bloom's Taxonomy: the practical tool</h2>
<p>Benjamin Bloom's framework for categorising cognitive skills is the most widely used tool for writing learning objectives, and for good reason — it is practical. The taxonomy organises thinking into six levels, from lower-order to higher-order:</p>
<ol>
  <li><strong>Remember</strong> – recall facts and basic information</li>
  <li><strong>Understand</strong> – explain ideas in your own words</li>
  <li><strong>Apply</strong> – use knowledge in a new situation</li>
  <li><strong>Analyse</strong> – break information into parts and examine relationships</li>
  <li><strong>Evaluate</strong> – make judgments based on criteria</li>
  <li><strong>Create</strong> – produce something new using knowledge and skills</li>
</ol>
<p>Each level has a set of action verbs associated with it. The key rule is simple: your learning objective must use a verb from the appropriate level, and your activities and assessments must demand the same level of thinking.</p>

<h2>Action verbs by level</h2>
<p>Here is a practical reference for Caribbean teachers, with verbs most useful for lesson planning:</p>
<p><strong>Remember:</strong> define, list, name, recall, identify, match, state, label</p>
<p><strong>Understand:</strong> describe, explain, summarise, paraphrase, classify, give examples</p>
<p><strong>Apply:</strong> calculate, solve, use, demonstrate, construct, produce, show</p>
<p><strong>Analyse:</strong> compare, contrast, distinguish, examine, break down, infer, organise</p>
<p><strong>Evaluate:</strong> justify, argue, assess, critique, defend, recommend, rank</p>
<p><strong>Create:</strong> design, develop, compose, plan, generate, produce, write</p>

<h2>The formula for a strong objective</h2>
<p>A reliable formula for writing learning objectives is: <strong>Students will be able to [action verb] + [specific content] + [condition or standard if needed].</strong></p>
<p>Examples built for Caribbean classrooms:</p>
<ul>
  <li>"Students will be able to <strong>identify</strong> the three branches of government in Trinidad and Tobago and state one function of each." (Remember)</li>
  <li>"Students will be able to <strong>explain</strong> how the trade winds influence rainfall patterns across the Caribbean." (Understand)</li>
  <li>"Students will be able to <strong>calculate</strong> the area and perimeter of compound shapes using the correct formula for each component." (Apply)</li>
  <li>"Students will be able to <strong>compare</strong> the narrative techniques used in two Caribbean short stories, identifying at least two similarities and two differences." (Analyse)</li>
  <li>"Students will be able to <strong>evaluate</strong> whether a given government policy effectively addresses food security in a small island developing state, using at least two pieces of evidence." (Evaluate)</li>
</ul>

<h2>How many objectives per lesson?</h2>
<p>One to three, as a rule. A single lesson cannot do everything. If you find yourself writing five or six objectives, you are either planning a unit rather than a lesson, or your objectives are so narrow they should be combined. Two well-written, measurable objectives will serve your students better than six vague ones.</p>

<h2>Connecting objectives to the Caribbean curriculum framework</h2>
<p>If you are teaching to a Ministry of Education syllabus or CXC framework, your learning objective should map directly to one of the stated learning outcomes in that document. This is what "curriculum alignment" means in practice — and it is what makes the difference between a lesson that feels productive and one that actually prepares students for their assessments.</p>
<p>EduCarib AI generates learning objectives automatically from the Caribbean curriculum framework, using the correct Bloom's verbs for each topic and level. You can edit them to fit your class, but the starting point is already aligned and measurable — which is most of the work done before you even open a blank page.</p>
""",
    },
]


def get_all_posts() -> list[dict]:
    """Return all posts sorted by date descending (most recent first)."""
    return sorted(POSTS, key=lambda p: p["date"], reverse=True)


def get_post_by_slug(slug: str) -> dict | None:
    """Return a single post by slug, or None if not found."""
    for post in POSTS:
        if post["slug"] == slug:
            return post
    return None