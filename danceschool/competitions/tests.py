import re
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Competition, Registration
from danceschool.core.models import DanceRole

from tabulate import tabulate 
from danceschool.competitions.views import calculate_skating

#import logging
#logging.basicConfig(level=logging.DEBUG)

'''
{
    'name': 'OBF 2021 JnJ',
    'judges':{
        'j1':{'name':'Jessy Kaiser','attr':('sp','l','spm','sf',),'pass':r'$@#$Vd3@$'},
        'j2':{'name':'Kuschi Kakuska','attr':('sp','l','sf',),'pass':r'Ab3f%O?06'},
        'j3':{'name':'Tanya Georgievska','attr':('sp','l','sf',),'pass':r'#@lv8l#p1'},
        'j4':{'name':'Kuva Kovalov','attr':('sp','f','spm','sf'),'pass':r'o&9A@54&V'},
        'j5':{'name':'Sondre Olsen-Bye','attr':('sp','f','sf','sfm'),'pass':r'XKrKD$&0j'},
    },
    'leaders':{
        1:'Oleksii Miroshnychenko',
        3:'Anton Morderer',
        5:'Alexander Belyy',
        7:'Konstantin Doychev',
        9:'Anton Kozachenko',
        13:'Martin Todorov',
        15:'Kostia Orlenko',
        17:'Hlib Dyachenko',
        19:'Vlad Volodko',
        21:'Hristian Georgiev',
        23:'Margarita Baykova',
        25:'Georgi Kostov',
        27:'Denis Rybak',
        29:'Niki Vedzhov',
        31:'Sasha Danilin',
    },
    'followers':{
        2:'',
        4:'',
        8:'',
        10:'',
        12:'',
        14:'',
        18:'',
        20:'',
        22:'',
        24:'',
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
},
'''

testing_jnj_data_list = [
{
    'name': 'Crown Bar JnJ',
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
},
]

class CompetitionTest(TestCase):
    def setUp(self):
        # Create superuser
        self.superuser = { 
            'username':'adminuser',
            'password':'admpass666',
            'email':'admin@example.com'
        }
        self.superuser['obj'] = User.objects.create_superuser(**self.superuser)
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
        for testing_jnj_data in testing_jnj_data_list:
            # Get or create users for judges 
            self.judge_profiles = {}
            for j,p in testing_jnj_data['judges'].items():
                jname = p['name'].split()
                profile = User.objects.create_user(
                    username=j,
                    password=p['pass'],
                    first_name=jname[0],
                    last_name=jname[1],
                )
                self.judge_profiles[j]=profile.id

            # Log in as admin (you can use Client.login)
            response = self.client.get('/admin/')
            self.assertEqual(response.status_code, 302)

            self.client.login(username=self.superuser['username'], password=self.superuser['password'])
            response = self.client.get('/admin/')
            self.assertEqual(response.status_code, 200)

            app_list = response.context_data.get('app_list', [])
            self.assertNotEqual(app_list, [])

            # Create a new competition with inline forms for judges
            judge_prefix = 'judge_set'
            reg_prefix = 'registration_set'
            competition_data = {
                'title': testing_jnj_data['name'],
                'stage': 'r',
                'comp_roles':(self.dance_roles['Leader'],self.dance_roles['Follower']),
                'staff':[self.superuser['obj'].id,],
                'finalists_number':len(testing_jnj_data['prelims']['finalists']['leaders']),
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
                jattr = testing_jnj_data['judges'][j]['attr']
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
                for cnum, competitor in testing_jnj_data[role.lower()+'s'].items():
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
                len(testing_jnj_data['leaders'])+len(testing_jnj_data['followers'])
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
            stage_points = testing_jnj_data['prelims']['points']
            legend = testing_jnj_data['prelims']['legend']
            for j,jdict in testing_jnj_data['judges'].items():
                # get all competitors with certain role and set 'no' by default
                jrole = 'followers' if 'f' in jdict['attr'] else 'leaders'
                jpoints = {f'competitor_{comp_num}':'no' for comp_num in testing_jnj_data[jrole]}

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
            for role,result in testing_jnj_data['prelims']['finalists'].items():
                self.assertSequenceEqual(finalists[role], result)
                #print(finalists[role])

            # Log in as admin and fill in draw results
            self.client.login(username=self.superuser['username'], password=self.superuser['password'])

            response = self.client.get(
                reverse('admin:competitions_competition_change',args=(comp.id,)))
            #with open('response_get.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 200)

            stage_pairs = testing_jnj_data['finals']['pairs']        
            competition_data['stage'] = 'f'
            competition_data = { # clean reg inline fields
                k:v for k,v in competition_data.items() 
                if not k.startswith(reg_prefix)
            }

            draw_data = {f:(l,int(p[1:])) for p,(l,f) in stage_pairs.items()}
            for inline_formset in response.context['inline_admin_formsets']:
                prefix = inline_formset.formset.prefix
                if prefix == reg_prefix:
                    competition_data[f'{prefix}-TOTAL_FORMS']=str(len(inline_formset.formset))
                    competition_data[f'{prefix}-INITIAL_FORMS']=str(len(inline_formset.formset))
                    competition_data[f'{prefix}-MIN_NUM_FORMS'] = '0'
                    competition_data[f'{prefix}-MAX_NUM_FORMS'] = '1000'
                    for form in inline_formset.formset:
                        for field in form:
                            html_name = field.html_name
                            name = field.html_name.split('-')[-1]
                            comp_num = form['comp_num'].value()
                            partner_dict = {int(partner.split(' ')[0]):id.value for id, partner in form['final_partner'].field.choices if id != ''}
                            if form[name].value() != None:
                                competition_data[html_name] = form[name].value()
                            if name == 'final_partner':
                                competition_data[html_name] = partner_dict[draw_data[comp_num][0]]
                            if name == 'final_heat_order':
                                competition_data[html_name] = draw_data[comp_num][1]      

            response = self.client.post(
                reverse('admin:competitions_competition_change',args=(comp.id,)),
                competition_data
            )
            #with open('response.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 302)
            self.client.logout()

            # submit finals results
            stage_points = testing_jnj_data['finals']['points']
            for j,jdict in testing_jnj_data['judges'].items():
                if 'sf' in jdict['attr']:
                    # apply judge points 
                    jpoints = {f'competitor_{stage_pairs[pair][1]}': point for pair,point in stage_points[j].items()}

                    # post data and check redirecton as successfull form submitting
                    self.client.login(username=j, password=jdict['pass'])
                    response = self.client.post(reverse('submit_results',args=(comp.id,)), jpoints)
                    self.assertEqual(response.status_code, 302)

                    # check finals_results view to trigger finals calculations on last judge applying
                    response = self.client.get(reverse('finals_results',args=(comp.id,)))
                    #with open(f'response_{j}.html','wt') as fl:
                    #    fl.write(response.content.decode())
                    self.assertEqual(response.status_code, 200)
                    self.client.logout()

            # make results visible to everyone
            self.client.login(username=self.superuser['username'], password=self.superuser['password'])
            competition_data['results_visible'] = True
            response = self.client.post(
                reverse('admin:competitions_competition_change',args=(comp.id,)),
                competition_data
            )
            #with open('response.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 302)
            self.client.logout()

            # check places
            stage_places = testing_jnj_data['finals']['places']
            response = self.client.get(reverse('finals_results',args=(comp.id,)))
            #with open('response_get.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 200)

            pattern = r'>(\d+)/(\d+)</td>'
            cur_place = 1
            for ln in response.content.decode().split('\n'):
                match = re.search(pattern, ln)
                if match:
                    pair_nums = (int(match.group(2)),int(match.group(1)))
                    self.assertSequenceEqual(stage_pairs[stage_places[cur_place]],pair_nums)
                    cur_place += 1

class SkatingCalculatorTest(TestCase):
    def test_sk(self):
        cases = [
            {
                'judges_list':['Jessy','Kuschi','Tanya','Kuva','Sondre'],
                'data_dict':{
                    'Oleksii & Vasilena': [ 4,6,4,4,3 ],
                    'Alexander & Dona': [ 6,7,5,6,6 ],
                    'Konstantin & Iliana': [ 7,5,6,7,7 ],
                    'Serhii & Arkadiia': [ 1,2,2,3,1 ],
                    'Martin & Viktoriia': [ 5,4,7,5,5 ],
                    'Hristian & Anna': [ 3,1,3,2,4 ],
                    'Niki & Iryna': [ 2,3,1,1,2 ],
                },
                'expected_results':[4,6,7,'1(1)',5,3,'2(2)'],
            },
            {
                'judges_list':['j1','j2','j3'],
                'data_dict':{
                    'c1':[1,2,3],
                    'c2':[2,3,1],
                    'c3':[3,1,2],
                    'c4':[4,4,4],
                },
                'expected_results':['1/2/3','1/2/3','1/2/3',4],
            },
            {
                'judges_list':['j1','j2','j3','j4','j5'],
                'data_dict':{
                    'c1':[3,1,1,2,3],
                    'c2':[5,3,2,1,2],
                    'c3':[1,2,4,3,4],
                    'c4':[2,4,3,4,1],
                    'c5':[4,5,5,5,5],
                },
                'expected_results':[1,2,'3(1)','4(2)',5],
            }
        ]
        
        for case in cases:
            sctable = calculate_skating(case['judges_list'],case['data_dict'])  
            sctable_results = [row[-1] for row in sctable[1:]]
            self.assertSequenceEqual(case['expected_results'],sctable_results,tabulate(sctable))

class StaffPermissionsTest(TestCase):
    def setUp(self):
        # Create superuser
        self.superuser = { 
            'username':'adminuser',
            'password':'admpass666',
            'email':'admin@example.com'
        }
        self.superuser['obj'] = User.objects.create_superuser(**self.superuser)
        # Create dance roles
        self.dance_roles = {}
        for ridx,role in enumerate(('Follower','Leader',)):
            role_ob = DanceRole.objects.create(
                name = role,
                pluralName = role + 's',
                order = ridx
            )
            self.dance_roles[role] = role_ob.id
        # Create Hosts group and add permissions to it
        hosts_group = Group.objects.create(name='Hosts')
        competition_content_type = ContentType.objects.get_for_model(Competition)
        permissions = Permission.objects.filter(
            content_type=competition_content_type,
            codename__in=[
                'add_competition',
                'change_competition',
                'view_competition',
                'delete_competition'
            ]
        )
        hosts_group.permissions.set(permissions)
        # Create 2 staff users
        self.staffusers = [
            { 
                'username':'staffuser1',
                'password':'staff1pass666',
                'email':'staff1@example.com'
            },
            { 
                'username':'staffuser2',
                'password':'staff2pass666',
                'email':'staff2@example.com'
            }
        ]
        for user in self.staffusers:
            user['obj'] = User.objects.create_user(**user,is_staff=True)
            user['obj'].groups.add(hosts_group)

    def test_sp(self):
        
        # Default required data for competition
        competition_data = {
            'stage': 'r',
            'comp_roles':(self.dance_roles['Leader'],self.dance_roles['Follower']),
            'finalists_number':5,
            'judge_set-TOTAL_FORMS': '0',
            'judge_set-INITIAL_FORMS': '0',
            'judge_set-MIN_NUM_FORMS': '0',
            'judge_set-MAX_NUM_FORMS': '1000',
            'registration_set-TOTAL_FORMS': '0',
            'registration_set-INITIAL_FORMS': '0',
            'registration_set-MIN_NUM_FORMS': '0',
            'registration_set-MAX_NUM_FORMS': '1000',
        }
        comp_obj = {}
        
        # create competitions with different staff users
        for user in self.staffusers:

            # check if user is staff
            self.assertTrue(user['obj'].is_staff)

            # competition name and staff list
            username = user['username']
            competition_data['title'] = f'{username}_comp_name'
            competition_data['staff']=[user['obj'].id,]

            # login
            self.client.login(username=user['username'], password=user['password'])
            response = self.client.get('/admin/')
            self.assertEqual(response.status_code, 200)

            app_list = response.context_data.get('app_list', [])
            self.assertNotEqual(app_list, [])

            # create competition
            response = self.client.get(reverse('admin:competitions_competition_add'))
            self.assertEqual(response.status_code, 200) 
            response = self.client.post(reverse('admin:competitions_competition_add'), competition_data)
            self.assertEqual(response.status_code, 302)

            # get competition object
            comp = Competition.objects.filter(title=competition_data['title']).first()
            comp_obj[user['obj']] = comp

            # logout
            self.client.logout()


        # check competitions access for different users
        for user in self.staffusers:

            # login
            self.client.login(username=user['username'], password=user['password'])
            response = self.client.get('/admin/')
            self.assertEqual(response.status_code, 200)

            for u, comp in comp_obj.items():
                response = self.client.get(
                    reverse('admin:competitions_competition_change',args=(comp.id,)))
                #with open('response_get.html','wt') as fl:
                #    fl.write(response.content.decode())
                self.assertEqual(response.status_code, 200 if u==user['obj'] else 302)

            # logout
            self.client.logout()

        # check superuser access
        self.client.login(username=self.superuser['username'], password=self.superuser['password'])
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

        for comp in comp_obj.values():
            response = self.client.get(
                reverse('admin:competitions_competition_change',args=(comp.id,)))
            #with open('response_get.html','wt') as fl:
            #    fl.write(response.content.decode())
            self.assertEqual(response.status_code, 200)

        # logout
        self.client.logout()
