from django.test import TestCase
from django.contrib.auth.models import User
from .models import Competition, Judge, Registration


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


class CompetitionRegistrationTest(TestCase):
    def setUp(self):
        # Create judges 
        self.judge_profiles = {}
        for j,p in crown_bar_jnj['judges'].items():
            jname = [p['name']].split()
            profile = User.objects.create_user(
                username=j,
                password=p['pass'],
                first_name=jname[0],
                last_name=jname[1],
            )
            self.judge_profiles[j:profile]

    def test_competition(self):
        # Log in as admin (you can use Client.login)
        self.client.login(username='toweeelie', password='SurStroMMing@666')

        # Create a new competition
        competition_data = {
            'title': 'Test Competition',
            'comp_roles':('Leader','Follower'),
            'finalists_number':len(crown_bar_jnj['prelims']['finalists']['leaders'])
        }

        response = self.client.post('/admin/testapp/competition/add/', competition_data)
        self.assertEqual(response.status_code, 302)  # Check for successful creation (HTTP 302)

        # register competitors
        comp = Competition.objects.get(title='Test Competition')
        for role in ('Leader','Follower'):
            for competitor in crown_bar_jnj[role.lower+'s'].values():
                response = self.client.post(f'/competitions/{comp.id}/register/', {
                    'first_name': competitor.split()[0],
                    'last_name': competitor.split()[1],
                    'email': 'noemail@example.com',
                    'role':role,
                })
                self.assertEqual(response.status_code, 302)  # Check for successful registration (HTTP 302)

        registered_competitors = Registration.objects.filter(comp=comp)
        self.assertEqual(registered_competitors.count(), len(crown_bar_jnj['leaders'])+len(crown_bar_jnj['followers']))

        # add judges
        for j,p in self.judge_profiles.items():
            jattr = crown_bar_jnj['judges'][j]['attr']
            args = {
                'profile':p,
                'comp':comp,
                'prelims':True,
                'prelims_role':'Follower' if 'f' in jattr else 'Leader'
            }
            if 'spm' in jattr:
                args['prelims_main_judge']= True
            if 'sf' in jattr:
                args['finals']=True
                if 'sfm' in jattr:
                    args['finals_main_judge']=True
            
            Judge.objects.create(**args)

        # change competition stage to prelims
        response = self.client.post(f'/admin/testapp/competition/{comp.id}/change/',{
            'stage':'p',
        })
        self.assertEqual(response.status_code, 302)

        # logout as admin
        self.client.logout()

        # apply prelims marks with judges accounts
        stage_points = crown_bar_jnj['prelims']['points']
        for j,jdict in crown_bar_jnj['judges'].items():
            jpass = jdict['pass']
            jrole = 'followers' if 'f' in jdict['attr'] else 'leaders'

            jpoints = {f'competitor_{comp_num}':stage_points[j][comp_num] for comp_num in crown_bar_jnj[jrole]}

            self.client.login(username=j, password=jpass)
            response = self.client.post(f'/competitions/{comp.id}/judging/', jpoints)
            self.assertEqual(response.status_code, 302)
            self.client.logout()


        # Log in as admin and fill in draw results
        self.client.login(username='toweeelie', password='SurStroMMing@666')

        self.client.logout()

