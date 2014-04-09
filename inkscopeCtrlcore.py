# Alpha O. Sall
# 04/04/2014

from flask import Flask, request, Response, render_template
app = Flask(__name__)#,template_folder='/var/www/inkscope/inkscopeAdm/')

import requests
from array import *
import sys
from urllib2 import HTTPError
import json
from bson.json_util import dumps


# import mongoJuiceCore
# import poolsCtrl



class Pools:
    """docstring for pools"""
    def __init__(self):
        self.name = None
        self.pg_num = None
        self.pgp_num = None
        self.size = None
        self.min_size = None
        self.crash_replay_interval = None
        self.crush_ruleset = None
        self.quota_max_objects = None
        self.quota_max_bytes = None
        

    def newpool_attribute(self, jsonform):
        
        jsondata = json.loads(jsonform)
        self.name = jsondata['pool_name']
        self.pg_num = jsondata['pg_num']
        self.pgp_num = jsondata['pg_placement_num']
        self.size = jsondata['size']
        self.min_size = jsondata['min_size']
        self.crash_replay_interval = jsondata['crash_replay_interval']
        self.crush_ruleset = jsondata['crush_ruleset']
        self.quota_max_objects = jsondata['quota_max_objects']
        self.quota_max_bytes = jsondata['quota_max_bytes']

    def savedpool_attribute(self, poolnum, jsonfile):
        ind = getindice(poolnum, jsonfile)
        r = jsonfile.json()
        self.name = r['output']['pools'][ind]['pool_name']
        self.pg_num = r['output']['pools'][ind]['pg_num']
        self.pgp_num = r['output']['pools'][ind]['pg_placement_num']
        self.size = r['output']['pools'][ind]['size']
        self.min_size = r['output']['pools'][ind]['min_size']
        self.crash_replay_interval = r['output']['pools'][ind]['crash_replay_interval']
        self.crush_ruleset = r['output']['pools'][ind]['crush_ruleset']
        self.quota_max_objects = r['output']['pools'][ind]['quota_max_objects']
        self.quota_max_bytes = r['output']['pools'][ind]['quota_max_bytes']

    #osd lspools    
    def show(self):
        r = requests.get('http://localhost:8080/ceph-rest-api/osd/lspools.json')
        return r.text

    def create(self):
        return requests.put('http://localhost:8080/ceph-rest-api/osd/pool/create?pool='+poolname+'&pg_num='+pg_num+'&pgp_num='+pgp_num)

    def delete(self):
        return requests.put('http://localhost:8080/ceph-rest-api/osd/pool/delete?pool='+poolname+'&sure=--yes-i-really-really-mean-it')


def getindice(id, jsondata):
    r = jsondata.json()
    mypoolsnum = array('i',[])
    for i in r['output']['pools']:
        mypoolsnum.append(i[u'pool'])
    if id not in  mypoolsnum:
        return "That pool's id does not exit"

    else:
        for i in range(len(mypoolsnum)):
            if mypoolsnum[i]==id:
                id=i
        return id

def getpoolname(ind, jsondata):
    r = jsondata.json()
    poolname = r['output']['pools'][ind]['pool_name']

    return str(poolname)

def geterrors(url, methods):
    try:
        if methods == 'GET':
            r = requests.get(url)
        else:
            r = requests.put(url)
    except HTTPError, e:
        return 'Error '+str(r.status_code) 
    else:
        return  'kjh'


@app.route('/pools/', methods=['GET','POST'])
@app.route('/pools/<int:id>', methods=['GET','DELETE','PUT'])
def pool_manage(id=None):
    if request.method == 'GET':
        if id == None:
            
            r = requests.get('http://localhost:8080/ceph-rest-api/osd/lspools.json')
             
            if r.status_code != 200:
                return Response(r.raise_for_status())
            else:
                return Response(r, mimetype='application/json')
        else:
            data = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
            if data.status_code != 200:
                return 'Error '+str(r.status_code)+' on the request getting pools'
            else:

                ind = getindice(id, data)
                id = ind
                if id == "That pool's id does not exit":
                    return id

                else:
                    skeleton = {'status':'','output':{}}
                    
                    r = data.json()
                    skeleton['status'] = r['status']
                    skeleton['output'] = r['output']['pools'][id]

                    result = json.dumps(skeleton)
                    return Response(result, mimetype='application/json')

    elif request.method =='POST':
        jsonform = request.form['json']
        newpool = Pools()
        newpool.newpool_attribute(jsonform)
        
        create_pool = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/create?pool='+newpool.name+'&pg_num='+str(newpool.pg_num)+'&pgp_num='+str(newpool.pgp_num))

        if create_pool.status_code != 200:
            return 'Error '+str(r.status_code)+' on creating pools'
        else:

            r = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
            r = r.json()
            nbpool = len(r['output']['pools'])

            
            poolcreated = Pools()

            poolcreated.name = r['output']['pools'][nbpool-1]['pool_name']
            poolcreated.size = r['output']['pools'][nbpool-1]['size']
            poolcreated.min_size = r['output']['pools'][nbpool-1]['min_size']
            poolcreated.crash_replay_interval = r['output']['pools'][nbpool-1]['crash_replay_interval']
            poolcreated.crush_ruleset = r['output']['pools'][nbpool-1]['crush_ruleset']
            poolcreated.quota_max_objects = r['output']['pools'][nbpool-1]['crush_ruleset']
            poolcreated.quota_max_bytes = r['output']['pools'][nbpool-1]['crush_ruleset']

            """ 
                set poool parameter

            """ 
            var_name= ['size', 'min_size', 'crash_replay_interval','crush_ruleset']
            param_to_set_list = [newpool.size, newpool.min_size, newpool.crash_replay_interval, newpool.crush_ruleset]
            default_param_list = [poolcreated.size, poolcreated.min_size, poolcreated.crash_replay_interval, poolcreated.crush_ruleset]

            for i in range(len(default_param_list)):
                if param_to_set_list[i] != default_param_list[i]:
                    r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/set?pool='+str(poolcreated.name)+'&var='+var_name[i]+'&val='+str(param_to_set_list[i])) 
                else:
                    pass

            """
                set object or byte limit on pool
            """
            field_name = ['max_objects','max_bytes']
            param_to_set = [newpool.quota_max_objects, newpool.quota_max_bytes]
            default_param = [poolcreated.quota_max_objects, poolcreated.quota_max_bytes]

            for i in range(len(default_param)):
                if param_to_set[i] != default_param[i]:
                    r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/set-quota?pool='+str(poolcreated.name)+'&field='+field_name[i]+'&val='+str(param_to_set[i])) 
                
                else:
                    pass        
            return None

    elif request.method == 'DELETE':
        r = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
        if r.status_code != 200:
            return 'Error '+str(r.status_code)+' on the request getting pools'
        else:
            r = r.json()

            data = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
            ind = getindice(id, data)
            id = ind

            poolname = r['output']['pools'][id]['pool_name']
            poolname = str(poolname)
            delete_request = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/delete?pool='+poolname+'&pool2='+poolname+'&sure=--yes-i-really-really-mean-it')
            return str(delete_request.status_code)

    else:


        # newpool = Pools()
        # newpool.getdata()
        jsondata = request.form['json']
        jsondata = json.loads(jsondata)
        pool_name = jsondata['pool_name']
        pg_num = jsondata['pg_num']
        pgp_num = jsondata['pg_placement_num']
        size = jsondata['size']
        min_size = jsondata['min_size']
        crash_replay_interval = jsondata['crash_replay_interval']
        crush_ruleset = jsondata['crush_ruleset']
        quota_max_objects = jsondata['quota_max_objects']
        quota_max_bytes = jsondata['quota_max_bytes']


        data = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
        if data.status_code != 200:
            return 'Error '+str(r.status_code)+' on the request getting pools'
        else:
            r = data.json()

            ind = getindice(id, data)
            id = ind

            nbpool = len(r['output']['pools'])
            poolname = r['output']['pools'][id]['pool_name']
            size_default = r['output']['pools'][id]['size']
            min_size_default = r['output']['pools'][id]['min_size']
            crash_replay_interval_default = r['output']['pools'][id]['crash_replay_interval']
            crush_ruleset_default = r['output']['pools'][id]['crush_ruleset']

            quota_max_objects_default = r['output']['pools'][id]['crush_ruleset']
            quota_max_bytes_default = r['output']['pools'][id]['crush_ruleset']

            '''rename the poolname'''

            if str(poolname) != str(pool_name):
                r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/rename?srcpool='+str(poolname)+'&destpool='+str(pool_name)) 
                poolname = str(pool_name)

            """ 
                set poool parameter

            """ 
            var_name= ['size', 'min_size', 'crash_replay_interval','crush_ruleset']
            param_to_set_list = [size, min_size, crash_replay_interval, crush_ruleset]
            default_param_list = [size_default, min_size_default, crash_replay_interval_default, crush_ruleset_default]

            for i in range(len(default_param_list)):
                if param_to_set_list[i] != default_param_list[i]:
                    r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/set?pool='+str(poolname)+'&var='+var_name[i]+'&val='+str(param_to_set_list[i])) 
                else:
                    pass

            """
                set object or byte limit on pool
            """
            field_name = ['max_objects','max_bytes']
            param_to_set = [quota_max_objects, quota_max_bytes]
            default_param = [quota_max_objects_default, quota_max_bytes_default]

            for i in range(len(default_param)):
                if param_to_set[i] != default_param[i]:
                    r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/set-quota?pool='+str(poolname)+'&field='+field_name[i]+'&val='+str(param_to_set[i])) 
                else:
                    pass        
            return str(r.status_code)

@app.route('/pools/<int:id>/snapshot', methods=['POST'])
def makesnapshot(id):
    data = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
    r = data.json()
    ind = getindice(id,data)
    id = ind

    poolname = r['output']['pools'][id]['pool_name']

    jsondata = request.form['json']
    jsondata = json.loads(jsondata)
    snap = jsondata['snapshot_name']
    r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/mksnap?pool='+str(poolname)+'&snap='+str(snap)) 
    return str(r.status_code)

@app.route('/pools/<int:id>/snapshot/<namesnapshot>', methods=['DELETE'])
def removesnapshot(id,namesnapshot):

    data = requests.get('http://localhost:8080/ceph-rest-api/osd/dump.json')
    r = data.json()
    ind = getindice(id,data)
    id = ind

    poolname = r['output']['pools'][id]['pool_name']

    try:
        r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/rmsnap?pool='+str(poolname)+'&snap='+str(namesnapshot))
    except HTTPException, e:
        return e    
    else:
        return r.content



# else:
#     pool_name = request.form['pool.name']
#     pg_num = request.form['pool.pg_num']
#     pgp_num = request.form['pool.pg_num']
#     r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/create?pool='+pool_name+'&pg_num='+pg_num+'&pgp_num='+pgp_num)
#     return 'hello'



# class Pools:
#     """docstring for pools"""
#     def __init__(self, pool_name, pg_num, pgp_num):
#         self.pool_name = pool_name
#         self.pg_num = pg_num
#         self.pgp_num = pgp_num
        

# #     def form(self):
# #         return "render_template('form/PoolsForm.html')"

# #     #osd lspools    
# #     def show(self):
# #         r = requests.get('http://localhost:8080/ceph-rest-api/osd/lspools.json')
# #         return Response(r, mimetype='application/json')

#     def create(self):

#         pool_name = request.form['pool_name']
#         pg_name = request.form['pg_num']
#         pgp_num = request.form['pgp_num']
        
#         r = requests.put('http://localhost:8080/ceph-rest-api/osd/pool/create?pool='+poolname+'&pg_num='+pg_num+'&pgp_num='+pgp_num)
#         return ''

#     def delete(self):
#         check = ''
#         return requests.put('http://localhost:8080/ceph-rest-api/osd/pool/delete?pool='+poolname+'&sure=--yes-i-really-really-mean-it')

# class Osd:
#     """docstring for Osd"""
#     def __init__(self):
#         self.uuid = ''

#     def form(self):
#         return "render_template('form/PoolsForm.html')"

#     def show(self):
#         r = requets.get('http://localhost:8080/ceph-rest-api/osd/ls?epoch=0')
#         return Response(r,mimetype='application/json')

#     def create(self):
#         return request.get('http://localhost:8080/ceph-rest-api/osd/crush/rule/list.json') 

# @app.route('/<myobject>/')
# def list(myobject):
#     if isinstance(myobject,Pools):
#         myobject.show()
#     elif isinstance(myobject, Osd):
#         myobject.show()
#     else:
#         return 'bad object'

# class Mon:
#     """docstring for Mon"""
#     def __init__(self, name, address):
#         self.name = name
#         self.address = address
        


                       
# # def create_obj(myobject):
# #     #if isinstance(myobject, Osd):
# #     #     myobject.name = request.form['name']
# #     #     myobject.pg_num = request.form['pg_num']
# #     #     myobject.pgp_num = request.form['pgp_num']
# #     if isinstance(myobject,Osd):
# #         r = requests.put('http://localhost:8080/ceph-rest-api/osd/create')
# #     else:
# #         return('hi')
# #     return 'dd'
#     #elif isinstance(myobject, mon):
#     #    return "do_something"

#     #elif isinstance(myobject, osd):
#         #return "do_something"

#     #elif isinstance(myobject, pg):
#     #    return "do_something"

#     #elif isinstance(myobject, rgw):
#     #    return "do_something"

#     #return "render_template('liste.html')"


# @app.route('/Osds/')
# @app.route('/Osds/<int:element>', methods=['GET','POST'])
# def show(element=None):
#     if request.method=='GET':
#         if element==None:
#             r = requets.get('http://localhost:8080/ceph-rest-api/osd/ls?epoch=0')
#         else:
#             r = requests.get('http://localhost:8080/ceph-rest-api/osd/find?id='+element)
#         return Response(r)

#     if request.method == 'POST':
#         r = requests.put('http://localhost:8080/ceph-rest-api/osd/create')

#     return Response(r)

# def listpool(element):
#     if request.method=='GET':
#         element = int(element)
#         if element==None:
#             r = requets.get('http://localhost:8080/ceph-rest-api/osd/lspools.json')
#             return element
#         else:
#             r = requests.get('http://localhost:8080/ceph-rest-api/osd/lspools.json?auid=%d'%element)
#             return "r.text"

#     else:
#         #r = requests.put('http://localhost:8080/ceph-rest-api/osd/create')
#         return "redirect(url_for('/Osds/')"


# @app.route('/osds/')
# @app.route('/osds/<element>', methods=['GET','POST'])
# def voir(element):
#     return show(element)

# @app.route('/pools/<element>', methods = ['GET', 'POST'])
# def voirpools(element):
#     return listpools(element)

































