# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post-installation hook to migrate existing data"""
    _logger.info("Running post-installation hook for sgc_assessment...")

    # Drop old email unique constraint (allows duplicate submissions)
    _drop_email_constraint(env)

    # Migrate candidate status for old records
    _migrate_candidate_status(env)

    # Ensure all candidates have access tokens
    _ensure_access_tokens(env)

    _logger.info("Post-installation hook completed successfully")


def _drop_email_constraint(env):
    """Drop the email unique constraint to allow duplicate submissions"""
    _logger.info("Dropping email unique constraint...")

    try:
        # Drop the constraint if it exists
        env.cr.execute("""
            ALTER TABLE assessment_candidate
            DROP CONSTRAINT IF EXISTS assessment_candidate_email_unique;
        """)
        env.cr.commit()
        _logger.info("✅ Email unique constraint dropped successfully (duplicate submissions now allowed)")
    except Exception as e:
        _logger.warning("Could not drop email constraint (may not exist): %s", str(e))
        # Don't fail the upgrade if constraint doesn't exist
        env.cr.rollback()


def _migrate_candidate_status(env):
    """Ensure all candidates have a valid status"""
    _logger.info("Migrating candidate status...")
    
    Candidate = env['assessment.candidate']
    
    # Find candidates without status (should not happen, but just in case)
    candidates_no_status = Candidate.search([('status', '=', False)])
    if candidates_no_status:
        _logger.info("Found %d candidates without status, setting to 'submitted'", len(candidates_no_status))
        candidates_no_status.write({'status': 'submitted'})
    
    # Update status based on related records
    candidates = Candidate.search([])
    for candidate in candidates:
        should_update = False
        new_status = candidate.status
        
        # If has AI score but status is still draft/submitted
        if candidate.ai_score_id and candidate.status in ('draft', 'submitted'):
            new_status = 'ai_scored'
            should_update = True
        
        # If has human review but status is ai_scored
        if candidate.human_review_ids and candidate.status == 'ai_scored':
            new_status = 'reviewed'
            should_update = True
        
        if should_update:
            _logger.info("Updating candidate %d status from %s to %s", candidate.id, candidate.status, new_status)
            candidate.write({'status': new_status})
    
    _logger.info("Migrated status for %d candidates", len(candidates))


def _ensure_access_tokens(env):
    """Ensure all candidates have access tokens"""
    _logger.info("Ensuring access tokens...")
    
    Candidate = env['assessment.candidate']
    candidates_no_token = Candidate.search([('access_token', '=', False)])
    
    if candidates_no_token:
        _logger.info("Found %d candidates without access tokens, generating...", len(candidates_no_token))
        for candidate in candidates_no_token:
            # Using protected method is intentional - this is a data migration hook
            candidate.write({'access_token': candidate._generate_access_token()})  # pylint: disable=protected-access
    
    _logger.info("Ensured access tokens for all candidates")
