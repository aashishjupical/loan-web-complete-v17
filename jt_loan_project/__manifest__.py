# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    "name": "The Complete Loan application with Website",
    "version": "17.0.0.0.3",
    'summary': 'A complete advanced package of loan ERP integrated with individual credit score,multiple API integration like google calender, goole meet, organisation identity verification',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.com',
    "category": "Industries",
    'external_dependencies': {
        'python': ['xmltodict','email-validator']
    },
    "depends": ['jt_loan_management',
                'project','website',
                'website_payment',
                'calendar',
                'appointment_calendar',
                #'google_meet_integration'
               ],
    "data": [  
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/terminate_wizard.xml',
        'wizard/upload_video.xml',
        'views/project_task.xml',
        'views/terminate_reason_view.xml',
        'views/tenure_month_view.xml',       
        'views/loan_application_history.xml',
        'views/res_config_view.xml',
        'views/res_partner_ext.xml',
        'views/product.xml',
        'data/mail_templates.xml',
        'template/home_page_inherit.xml',
        'template/header_footer.xml',
        'template/login.xml',
        'template/create_account.xml',
        'template/sign_up_tmp.xml',
        'template/demo.xml',
        'template/index.xml',
        'template/front_document.xml',
        'template/back_document.xml',
        'template/photo_document.xml',
        'template/review_idenity.xml',
        'template/identity_success.xml',
        'template/submit_doc_dashboard.xml',
        'template/approve_loan_dashboard.xml',
        'template/per_emergency_info.xml',
        'template/emp_bank_acc_info.xml',
        'template/doc_self_emp.xml',
        'template/doc_salarised_emp.xml',
        'template/review_submit_doc.xml',
        'template/submit_doc_success.xml',
        'template/loan_approval_success.xml',
        'template/loan_approval_rejected.xml',
        'template/start_attestation.xml',
        'template/video_attestation.xml',
        'template/review_agree_attestation.xml',
        'template/attestation_sucess.xml',
        'template/esign_dashboard.xml',
        'template/esign_agreement.xml',
        'template/esign_success.xml',
        'template/product_page.xml',
        'template/active_loan_detail.xml',
        'template/calculate_interest.xml',
        'template/in_person_attestion.xml',
        'template/in_person_attestion_sch.xml',
        'data/demo_data.xml',
        ],
     'assets': {
        'web.assets_frontend': [
            '/jt_loan_project/static/src/css/plugins/all.min.css',
            '/jt_loan_project/static/src/css/plugins/swiper-bundle.min.css',
            '/jt_loan_project/static/src/css/index.css',
            '/jt_loan_project/static/src/css/login.css',
            '/jt_loan_project/static/src/css/common.css',
            '/jt_loan_project/static/src/css/in_person_attestation.css',
            '/jt_loan_project/static/src/css/in_person_attestation_sch.css',
            '/jt_loan_project/static/src/css/front_doc.css',
            '/jt_loan_project/static/src/css/doc_salarised_emp.css',
            '/jt_loan_project/static/src/css/apply_now.css',
            '/jt_loan_project/static/src/css/identity_success.css',
            '/jt_loan_project/static/src/css/review_identity.css',
            '/jt_loan_project/static/src/css/get_user_info.css',
            '/jt_loan_project/static/src/css/emp_bank_acc_info.css',
            '/jt_loan_project/static/src/css/product_page.css',
            '/jt_loan_project/static/src/css/video_attestation.css',
            '/jt_loan_project/static/src/css/review_agree.css',
            '/jt_loan_project/static/src/css/active_loan.css',
            # '/jt_loan_project/static/src/js/plugins/swiper-bundle.min.js',
            '/jt_loan_project/static/src/js/script.js',
            '/jt_loan_project/static/src/js/attestation.js',
            '/jt_loan_project/static/src/js/form_validation.js',
            # '/jt_loan_project/static/src/js/button_click.js',
            '/jt_loan_project/static/src/js/interest_rate_calculation.js',
            '/jt_loan_project/static/src/js/country_state_filter.js',
            # '/jt_loan_project/static/src/js/plugins/jquery.min.js',
            # '/jt_loan_project/static/src/js/plugins/all.min.js',
        ],
    },

    'demo': [],
    'currency': "USD",
    'license': 'OPL-1',
    'images': ['static/description/poster_image.gif'],
    'installable': True,
}
