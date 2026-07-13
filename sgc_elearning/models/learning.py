# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LearningChapter(models.Model):
    """A learning chapter groups related sections and assets."""
    _name = 'learning.chapter'
    _description = 'Learning Chapter'
    _order = 'sequence, id'

    name = fields.Char(string='Chapter Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Html(string='Description', translate=True)
    section_ids = fields.One2many(
        'learning.section', 'chapter_id', string='Sections')
    asset_ids = fields.One2many(
        'learning.asset', 'chapter_id', string='Assets')
    badge_id = fields.Many2one('learning.badge', string='Completion Badge')
    is_published = fields.Boolean(string='Published', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningSection(models.Model):
    """A section is a sub-part of a chapter containing learning content."""
    _name = 'learning.section'
    _description = 'Learning Section'
    _order = 'sequence, id'

    name = fields.Char(string='Section Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    chapter_id = fields.Many2one(
        'learning.chapter', string='Chapter', required=True, ondelete='cascade')
    content = fields.Html(string='Content', translate=True)
    content_type = fields.Selection([
        ('text', 'Text'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('quiz', 'Quiz'),
    ], string='Content Type', default='text', required=True)
    quiz_id = fields.Many2one('learning.quiz', string='Quiz')
    duration_minutes = fields.Integer(string='Duration (minutes)', default=0)
    is_published = fields.Boolean(string='Published', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningAsset(models.Model):
    """Supplementary asset files attached to a chapter."""
    _name = 'learning.asset'
    _description = 'Learning Asset'
    _order = 'sequence, id'

    name = fields.Char(string='Asset Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    chapter_id = fields.Many2one(
        'learning.chapter', string='Chapter',
        required=True, ondelete='cascade')
    asset_type = fields.Selection([
        ('file', 'File'),
        ('link', 'Link'),
        ('image', 'Image'),
    ], string='Asset Type', default='file', required=True)
    file = fields.Binary(string='File')
    url = fields.Char(string='URL')
    description = fields.Text(string='Description', translate=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningQuiz(models.Model):
    """A quiz tests user knowledge on chapter/section content."""
    _name = 'learning.quiz'
    _description = 'Learning Quiz'
    _order = 'sequence, id'

    name = fields.Char(string='Quiz Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Html(string='Description', translate=True)
    question_ids = fields.One2many(
        'learning.quiz.question', 'quiz_id', string='Questions')
    passing_score = fields.Float(
        string='Passing Score (%)', default=70.0)
    attempt_limit = fields.Integer(string='Max Attempts', default=0,
                                   help='0 = unlimited')
    time_limit_minutes = fields.Integer(
        string='Time Limit (minutes)', default=0,
        help='0 = no time limit')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningQuizQuestion(models.Model):
    """Questions belonging to a quiz."""
    _name = 'learning.quiz.question'
    _description = 'Quiz Question'
    _order = 'sequence, id'

    name = fields.Char(string='Question', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    quiz_id = fields.Many2one(
        'learning.quiz', string='Quiz', required=True, ondelete='cascade')
    question_type = fields.Selection([
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ], string='Question Type', default='multiple_choice', required=True)
    option_ids = fields.One2many(
        'learning.quiz.option', 'question_id',
        string='Options')
    explanation = fields.Html(string='Explanation', translate=True)


class LearningQuizOption(models.Model):
    """Answer options for quiz questions."""
    _name = 'learning.quiz.option'
    _description = 'Quiz Option'
    _order = 'sequence, id'

    name = fields.Char(string='Option', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one(
        'learning.quiz.question', string='Question',
        required=True, ondelete='cascade')
    is_correct = fields.Boolean(string='Correct Answer', default=False)


class LearningQuizAttempt(models.Model):
    """Records a user's attempt at a quiz."""
    _name = 'learning.quiz.attempt'
    _description = 'Quiz Attempt'
    _rec_name = 'display_name'

    quiz_id = fields.Many2one(
        'learning.quiz', string='Quiz', required=True, ondelete='cascade')
    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        default=lambda self: self.env.user)
    answer_ids = fields.One2many(
        'learning.quiz.answer', 'attempt_id', string='Answers')
    score = fields.Float(
        string='Score (%)', compute='_compute_score', store=True)
    passed = fields.Boolean(
        string='Passed', compute='_compute_score', store=True)
    started_at = fields.Datetime(
        string='Started At', default=fields.Datetime.now)
    completed_at = fields.Datetime(string='Completed At')
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='State', default='in_progress', required=True)

    @api.depends('answer_ids.is_correct')
    def _compute_score(self):
        for attempt in self.attempt_ids:
            total = len(attempt.answer_ids)
            correct = len(attempt.answer_ids.filtered('is_correct'))
            attempt._compute_score_values(total, correct)

    def _compute_score_values(self, total, correct):
        """Separated for override. Compute score and passed."""
        if total == 0:
            self.score = 0.0
            self.passed = False
        else:
            self.score = round((correct / total) * 100, 2)
            self.passed = self.score >= self.quiz_id.passing_score

    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('quiz_id', 'user_id', 'started_at')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"{rec.quiz_id.name} - {rec.user_id.display_name}"
                f" ({rec.started_at})"
            )


class LearningQuizAnswer(models.Model):
    """Individual answer given during a quiz attempt."""
    _name = 'learning.quiz.answer'
    _description = 'Quiz Answer'

    attempt_id = fields.Many2one(
        'learning.quiz.attempt', string='Attempt',
        required=True, ondelete='cascade')
    question_id = fields.Many2one(
        'learning.quiz.question', string='Question', required=True)
    selected_option_id = fields.Many2one(
        'learning.quiz.option', string='Selected Option')
    short_answer_text = fields.Text(string='Answer Text')
    is_correct = fields.Boolean(
        string='Correct', compute='_compute_is_correct', store=True)

    @api.depends('selected_option_id', 'question_id', 'short_answer_text')
    def _compute_is_correct(self):
        for rec in self:
            if rec.selected_option_id:
                rec.is_correct = rec.selected_option_id.is_correct
            else:
                rec.is_correct = False


class LearningBadge(models.Model):
    """Achievement badge awarded on milestone completion."""
    _name = 'learning.badge'
    _description = 'Learning Badge'

    name = fields.Char(string='Badge Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    image = fields.Binary(string='Badge Image')
    required_chapter_ids = fields.Many2many(
        'learning.chapter', string='Required Chapters')
    required_quiz_ids = fields.Many2many(
        'learning.quiz', string='Required Quizzes')
    user_ids = fields.Many2many(
        'res.users', 'learning_badge_user_rel',
        'badge_id', 'user_id', string='Awarded Users')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningLeaderboard(models.Model):
    """Tracks top-performing learners."""
    _name = 'learning.leaderboard'
    _description = 'Learning Leaderboard'
    _order = 'score desc'

    user_id = fields.Many2one(
        'res.users', string='User', required=True)
    score = fields.Float(string='Score', default=0.0)
    quizzes_passed = fields.Integer(string='Quizzes Passed', default=0)
    total_attempts = fields.Integer(string='Total Attempts', default=0)
    last_activity = fields.Datetime(string='Last Activity')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class LearningCertificate(models.Model):
    """Certificate awarded upon completing a learning path."""
    _name = 'learning.certificate'
    _description = 'Learning Certificate'
    _rec_name = 'display_name'

    user_id = fields.Many2one(
        'res.users', string='User', required=True)
    chapter_ids = fields.Many2many(
        'learning.chapter', string='Completed Chapters')
    quiz_ids = fields.Many2many(
        'learning.quiz', string='Completed Quizzes')
    completion_date = fields.Datetime(
        string='Completion Date', default=fields.Datetime.now)
    certificate_code = fields.Char(
        string='Certificate Code', readonly=True,
        default=lambda self: self._generate_code())
    is_valid = fields.Boolean(string='Valid', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)

    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('user_id', 'completion_date')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"Certificate - {rec.user_id.display_name}"
                f" ({rec.completion_date})"
            )

    @api.model
    def _generate_code(self):
        """Generate a unique certificate verification code."""
        import secrets
        return 'CERT-' + secrets.token_hex(8).upper()


class LearningProgress(models.Model):
    """Tracks per-user progress through learning content."""
    _name = 'learning.progress'
    _description = 'Learning Progress'

    user_id = fields.Many2one(
        'res.users', string='User', required=True)
    chapter_id = fields.Many2one(
        'learning.chapter', string='Chapter', required=True)
    section_id = fields.Many2one(
        'learning.section', string='Section', ondelete='cascade')
    completed = fields.Boolean(string='Completed', default=False)
    progress_percent = fields.Float(
        string='Progress (%)', default=0.0)
    time_spent_minutes = fields.Integer(
        string='Time Spent (minutes)', default=0)
    last_access_date = fields.Datetime(
        string='Last Access', default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)

    _check_progress_unique = models.Constraint(
        'UNIQUE(user_id, chapter_id, section_id)',
        'Progress for this section already exists for this user!',
    )
