#import os
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school.settings")
#import django
#django.setup()
import re
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Competition, Judge, Registration
from danceschool.core.models import DanceRole
from django.core.exceptions import ValidationError

from django.forms.formsets import BaseFormSet
#import logging
#logging.basicConfig(level=logging.DEBUG)

crown_bar_jnj ={
    'judges':{
        'j1':{'name':'Марія Тітова','attr':('sp','l','spm','sf',),'pass':r'$@#$Vd3@$'},
        'j2':{'name':'Світлана Матових','attr':('sp','l','sf',),'pass':r'Ab3f%O?06'},
        'j3':{'name':'Саша Мосійчук','attr':('sp','l','sf',),'pass':r'#@lv8l#p1'},
        'j4':{'name':'СергійБ Безуглий','attr':('sp','f','spm','sf'),'pass':r'o&9A@54&V'},
        'j5':{'name':'Максим Болгов','attr':('sp','f','sf','sfm'),'pass':r'XKrKD$&0j'},
        'j6':{'name':'Сергій Ковальов','attr':('sp','f'),'pass':r'@41G939K6'},
    },
    'leaders':{
        1:'Влад Володько',
        3:'Антон Мордерер',
        5:'Влад Денисенко',
        7:'Денис Герасименко',
        9:'Ярослав Щербак',
        11:'Богдан Левченко',
        13:'Антон Дрейман',
        15:'Андрій Кислюк',
        17:'Олексій Мірошниченко',
        19:'Костянтин Гірлянд',
        21:'Костя Орленко',
        #23:'Максим РДС',
    },
    'followers':{
        2:'Катя Бенке',
        4:'Єва Місілюк',
        6:'Ксюша Венедиктова',
        8:'Яна Завгородня',
        10:'Ольга Коваленко',
        12:'Настя Мурга',
        14:'Олена Дорош',
        16:'Катя Безверха',
        18:'Наталя Гірлянд',
        20:'Даша Трофіменко',
        22:'Вова Лозовий',
        #24:'Ліза РДС',
    },
    'prelims':{
        'points':{
            'j1':{1:'Mb',3:'Y',7:'Y',17:'Y',19:'Mb',21:'Y'},
            'j2':{3:'Y',7:'Y',17:'Y',21:'Y',5:'Mb',19:'Mb'},
            'j3':{3:'Y',7:'Y',17:'Y',21:'Mb',1:'Y',5:'Mb'},
            'j4':{2:'Y',14:'Y',8:'Y',20:'Y',12:'Mb',16:'Mb'},
            'j5':{2:'Y',14:'Y',22:'Y',20:'Mb',12:'Mb',18:'Y'},
            'j6':{2:'Y',14:'Mb',8:'Y',22:'Y',20:'Mb',12:'Y'},
        },
        'legend':{'Y':'yes','Mb':'maybe'},
        'finalists':{
            'leaders':(1,3,7,17,21),
            'followers':(2,8,14,20,22),
        },
    },
    'finals':{
        'pairs':{
            'p1':(21,20),
            'p2':(7,14),
            'p3':(3,8),
            'p4':(1,2),
            'p5':(17,22),
        },
        'points':{
            'j1':{'p1':2,'p2':1,'p3':4,'p4':5,'p5':3},
            'j2':{'p1':2,'p2':3,'p3':4,'p4':5,'p5':1},
            'j3':{'p1':4,'p2':5,'p3':2,'p4':3,'p5':1},
            'j4':{'p1':4,'p2':5,'p3':1,'p4':2,'p5':3},
            'j5':{'p1':4,'p2':2,'p3':3,'p4':5,'p5':1},
        },
        'places':{1:'p5',2:'p3',3:'p2',4:'p1',5:'p4'},
    },
}


class CompetitionTest(TestCase):
    def setUp(self):
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='adminuser',
            password='admpass666',
            email='admin@example.com'
        )
        # Create judges 
        self.judge_profiles = {}
        for j,p in crown_bar_jnj['judges'].items():
            jname = p['name'].split()
            profile = User.objects.create_user(
                username=j,
                password=p['pass'],
                first_name=jname[0],
                last_name=jname[1],
            )
            self.judge_profiles[j]=profile.id
        # Create dance roles
        self.dance_roles = {}
        for ridx,role in enumerate(('Follower','Leader',)):
            role_ob = DanceRole.objects.create(
                name = role,
                pluralName = role + 's',
                order = ridx
            )
            self.dance_roles[role] = role_ob.id

    def test_competition(self):
        # Log in as admin (you can use Client.login)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

        self.client.login(username='adminuser', password='admpass666')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

        app_list = response.context_data.get('app_list', [])
        self.assertNotEqual(app_list, [])

        # Create a new competition with inline forms for judges
        judge_prefix = 'judge_set'
        reg_prefix = 'registration_set'
        competition_data = {
            'title': 'Test Competition',
            'stage': 'r',
            'comp_roles':(self.dance_roles['Leader'],self.dance_roles['Follower']),
            'finalists_number':len(crown_bar_jnj['prelims']['finalists']['leaders']),
            f'{judge_prefix}-TOTAL_FORMS': str(len(self.judge_profiles)),
            f'{judge_prefix}-INITIAL_FORMS': '0',
            f'{judge_prefix}-MIN_NUM_FORMS': '0',
            f'{judge_prefix}-MAX_NUM_FORMS': '1000',
            f'{reg_prefix}-TOTAL_FORMS': '0',
            f'{reg_prefix}-INITIAL_FORMS': '0',
            f'{reg_prefix}-MIN_NUM_FORMS': '0',
            f'{reg_prefix}-MAX_NUM_FORMS': '1000',
        }

        # add judges
        for i,(j,p) in enumerate(self.judge_profiles.items()):
            jattr = crown_bar_jnj['judges'][j]['attr']
            args = {
                'profile':p,
                'prelims':True,
                'prelims_role':self.dance_roles['Follower'] if 'f' in jattr else self.dance_roles['Leader']
            }
            if 'spm' in jattr:
                args['prelims_main_judge']= True
            if 'sf' in jattr:
                args['finals']=True
                if 'sfm' in jattr:
                    args['finals_main_judge']=True
            for k,v in args.items():
                competition_data[f'{judge_prefix}-{i}-{k}'] = v

        response = self.client.get(reverse('admin:competitions_competition_add'))
        self.assertEqual(response.status_code, 200) 
        response = self.client.post(reverse('admin:competitions_competition_add'), competition_data)
        self.assertEqual(response.status_code, 302)

        # register competitors
        comp = Competition.objects.filter(title=competition_data['title']).first()
        for role in ('Leader','Follower'):
            for cnum, competitor in crown_bar_jnj[role.lower()+'s'].items():
                response = self.client.post(
                    reverse('register_competitor',args=(comp.id,)), 
                    {
                        'first_name': competitor.split()[0],
                        'last_name': competitor.split()[1],
                        'email': 'noemail@example.com',
                        'comp_role':self.dance_roles[role],
                    }
                )
                #with open('response.html','wt') as fl:
                #    fl.write(response.content.decode())
                self.assertEqual(response.status_code, 200)  # no redirection here
                
                # check if assigned number is indeed the value from the table
                pattern = r'Your number is: (\d+)'
                match = re.search(pattern, response.content.decode())
                assingned_number = int(match.group(1))
                self.assertEqual(assingned_number, cnum)

        registered_competitors = Registration.objects.filter(comp=comp).all()
        self.assertEqual(
            registered_competitors.count(), 
            len(crown_bar_jnj['leaders'])+len(crown_bar_jnj['followers'])
        )

        # check-in competitors and change competition stage to prelims
        response = self.client.get(
            reverse('admin:competitions_competition_change',args=(comp.id,)))
        #with open('response_get.html','wt') as fl:
        #    fl.write(response.content.decode())
        self.assertEqual(response.status_code, 200)
            
        competition_data['stage'] = 'p'
        for inline_formset in response.context['inline_admin_formsets']:
            prefix = inline_formset.formset.prefix
            competition_data[f'{prefix}-TOTAL_FORMS']=str(len(inline_formset.formset))
            competition_data[f'{prefix}-INITIAL_FORMS']=str(len(inline_formset.formset))
            for form in inline_formset.formset:
                for field in form:
                    html_name = field.html_name
                    name = field.html_name.split('-')[-1]
                    if form[name].value() != None:
                        competition_data[html_name] = form[name].value()
                        if prefix == reg_prefix and name == 'comp_checked_in':
                            competition_data[html_name] = True

        response = self.client.post(
            reverse('admin:competitions_competition_change',args=(comp.id,)),
            competition_data
        )
        #with open('response.html','wt') as fl:
        #    fl.write(response.content.decode())
        self.assertEqual(response.status_code, 302)

        # logout as admin
        self.client.logout()

        # apply prelims marks with judges accounts
        stage_points = crown_bar_jnj['prelims']['points']
        legend = crown_bar_jnj['prelims']['legend']
        for j,jdict in crown_bar_jnj['judges'].items():
            # get all competitors with certain role and set 'no' by default
            jrole = 'followers' if 'f' in jdict['attr'] else 'leaders'
            jpoints = {f'competitor_{comp_num}':'no' for comp_num in crown_bar_jnj[jrole]}

            # apply judge points 
            for comp_num,point in stage_points[j].items():
                jpoints[f'competitor_{comp_num}'] = legend[point]

            # post data and check redirecton as successfull form submitting
            self.client.login(username=j, password=jdict['pass'])
            response = self.client.post(reverse('submit_results',args=(comp.id,)), jpoints)
            self.assertEqual(response.status_code, 302)

            # check prelims_results view to trigger prelims calculations on last judge applying
            response = self.client.get(reverse('prelims_results',args=(comp.id,)))
            #with open(f'response_{j}.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 200)
            self.client.logout()

        # check finalists list
        response = self.client.get(reverse('prelims_results',args=(comp.id,)))
        #with open('prelims_results.html','wt') as fl:
        #    fl.write(response.content.decode())
        self.assertEqual(response.status_code, 200)

        pattern = r'>(\d+)</td>'

        finalists = {'leaders':[],'followers':[]}
        for ln in response.content.decode().split('\n'):
            if 'Leaders' in ln:
                role = 'leaders'
            if 'Followers' in ln:
                role = 'followers'
            match = re.search(pattern, ln)
            if match:
                finalists[role].append(int(match.group(1)))
        for role,result in crown_bar_jnj['prelims']['finalists'].items():
            self.assertSequenceEqual(finalists[role], result)


'''
        # Log in as admin and fill in draw results
        self.client.login(username='adminuser', password='admpass666')

        self.client.logout()

'''