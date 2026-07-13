# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

from odoo import http
from odoo.addons.survey.controllers import main
from odoo.http import request


class Survey(main.Survey):
    """Inherits the class survey to super the controller"""

    @http.route('/survey/start/<string:survey_token>', type='http',
                auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False,
                     **post):
        """Inherits the method survey_start to check whether the survey
        appraisal is cancelled, done or has not started"""
        res = super(
            Survey, self).survey_start(
            survey_token=survey_token, answer_token=answer_token, email=email, **post)
        access_data = self._get_access_data(survey_token, answer_token,
                                            ensure_token=False)
        if access_data.get('answer_sudo').appraisal_id:
            if access_data.get('answer_sudo').appraisal_id.stage_id.name == "Cancel":
                return request.render("oh_appraisal.appraisal_canceled",
                                      {'survey': access_data.get('survey_sudo')})
            elif access_data.get('answer_sudo').appraisal_id.stage_id.name == "Done":
                return request.render("oh_appraisal.appraisal_done",
                                      {'survey': access_data.get(
                                          'survey_sudo')})
            elif access_data.get('answer_sudo').appraisal_id.stage_id.name == "To Start":
                return request.render("oh_appraisal.appraisal_draft",
                                      {'survey': access_data.get(
                                          'survey_sudo')})
        return res

