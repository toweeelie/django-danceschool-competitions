"""
Default Django settings fo

Generated by 'django-admin startproject' using Django 1.10.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# This line imports a large number of defaults, so that
# they do not need to be specified here directly.
# You may always override these defaults below.
from danceschool.default_settings import *

# This line is required by Django CMS to determine default URLs
# for pages.
SITE_ID = 1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'g8y64q4po6bcx7x57h_fgh48^r)fizrn)&8u1m7zptq%xssas%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: ALLOWED_HOSTS must be updated for production
# to permit public access of the site.
ALLOWED_HOSTS = ['127.0.0.1', 'localhost','testserver','hotboogie.com.ua']


# Application definition

INSTALLED_APPS = [
    # The CMS App goes first so that it will find plugins in other installed apps
    'cms',

    # The dynamic preferences app goes second so that it will find and register
    # project preferences in other installed apps
    'dynamic_preferences',

    'danceschool.competitions',

    # ## This is the core app of the django-danceschool project that
    # ## is required for all installations:
    'danceschool.core',

    # These are required for the CMS
    'menus',
    'sekizai',
    'treebeard',

    # Django-admin-sortable permits us to drag and drop sort page content items
    'adminsortable2',

    # Django-allauth is used for better authentication options
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',

    # For rich text in Django CMS
    'ckeditor_filebrowser_filer',
    'djangocms_text_ckeditor',

    # For picking colors
    'colorful',

    # This helps to make forms pretty
    'crispy_forms',

    # For Bootstrap 4 plugins and theme functionality
    'djangocms_icon',
    'djangocms_link',
    'djangocms_picture',
    'djangocms_bootstrap4',
    'djangocms_bootstrap4.contrib.bootstrap4_alerts',
    'djangocms_bootstrap4.contrib.bootstrap4_badge',
    'djangocms_bootstrap4.contrib.bootstrap4_card',
    'djangocms_bootstrap4.contrib.bootstrap4_carousel',
    'djangocms_bootstrap4.contrib.bootstrap4_collapse',
    'djangocms_bootstrap4.contrib.bootstrap4_content',
    'djangocms_bootstrap4.contrib.bootstrap4_grid',
    'djangocms_bootstrap4.contrib.bootstrap4_jumbotron',
    'djangocms_bootstrap4.contrib.bootstrap4_link',
    'djangocms_bootstrap4.contrib.bootstrap4_listgroup',
    'djangocms_bootstrap4.contrib.bootstrap4_media',
    'djangocms_bootstrap4.contrib.bootstrap4_picture',
    'djangocms_bootstrap4.contrib.bootstrap4_tabs',
    'djangocms_bootstrap4.contrib.bootstrap4_utilities',

    # Autocomplete overrides some admin features so it goes here (above admin)
    'dal',
    'dal_select2',

    # This allows for custom date range filtering of financials, etc.
    'rangefilter',

    # Makes Django CMS prettier
    'djangocms_admin_style',

    # This allows for PDF export of views
    'easy_pdf',

    # Django-filer allows for file and image management
    'easy_thumbnails',
    'filer',

    # This permits simple task scheduling
    'huey.contrib.djhuey',

    # Django-polymorphic is used for Event multi-table inheritance
    'polymorphic',

    'parler',
    
    # Finally, the Django contrib apps needed for this project and
    # its dependencies
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    

]

MIDDLEWARE = [
    # This middleware is required by Django CMS for intelligent reloading on updates.
    'cms.middleware.utils.ApphookReloadMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # These pieces of middleware are required by Django CMS
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
]

ROOT_URLCONF = 'school.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            # List of callables that know how to import templates from various sources.
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
                'danceschool.core.context_processors.site',
            ],
            'debug': False,
        },
    }
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '465'
EMAIL_HOST_USER = 'noemail@example.com'
EMAIL_HOST_PASSWORD = 'pass1!'
# EMAIL_USE_TLS = True
EMAIL_USE_SSL = True

WSGI_APPLICATION = 'school.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGES = [
  ('en', u'EN'),
  ('uk', u'UA'),
]

PARLER_LANGUAGES = {
    1: (
        {'code': 'en',},
        {'code': 'uk',},
    ),
    'default': {
        'fallbacks': ['en'],          # defaults to PARLER_DEFAULT_LANGUAGE_CODE
        'hide_untranslated': False,   # the default; let .active_translations() return fallbacks too.
    }
}

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'Europe/Kiev'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static') 
STATIC_URL = '/static/'

# User uploaded files (e.g. images)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# If the danceschool.backups app is enabled, this setting defines the location
# where backups are saved.
BACKUP_LOCATION = os.path.join(BASE_DIR, 'backups')
