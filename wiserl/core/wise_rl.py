# -- coding: utf-8 --

import ray
import time
import uuid
from  .registre_server import RegistreServer
from  .runner import Runner
from  .agent import Agent

#ray.init()

class WiseRL(object):
    def __init__(self):
        self.registre =  RegistreServer.remote()
    def makeRunner(self, name,Runner,num =1):
        for i in range(num):
            runner =ray.remote(Runner).remote(local_rank=i)
            self.registre.addRunner.remote(name,runner)
            runner.setRegistre.remote(self.registre)
        retref = self.registre.getAllRunner.remote(name)
        return ray.get(retref)

    def getRunner(self, name):
        return ray.get(self.registre.getRunner.remote(name))

    def makeAgent(self,name,agent_class,net_class,n_states ,n_actions,config=None,num=1, sync=True) :
        copy_name= None
        copy_agent = None
        if sync == False:
            copy_name="_wise_copy_" + name + str(uuid.uuid1())
            copy_agent =ray.remote(agent_class).remote(net_class,n_states,n_actions,config,sync)
            self.registre.addAgent.remote(copy_name,copy_agent,copy_agent)
            copy_agent.setRegistre.remote(self.registre) 
        for i in range(num):
            agent =ray.remote(agent_class).remote(net_class,n_states,n_actions,config,sync)
            self.registre.addAgent.remote(name,agent,copy_agent)
            agent.setRegistre.remote(self.registre)
            if sync == False:
                agent.setCopyName.remote(copy_name)
        retref = self.registre.getAllAgent.remote(name)
        return ray.get(retref)

    def makeSACAgent(self, name, agent_class, actor_net, value_net, q_net, n_states, n_actions, config=None, num=1,
                     sync=True):
        copy_name = None
        if sync is not True:
            copy_name = "_wise_copy_" + name + str(uuid.uuid1())
        for i in range(num):
            agent = ray.remote(agent_class).remote(actor_net, value_net, q_net, n_states, n_actions, config, sync)
            self.registre.addAgent.remote(name, agent)
            agent.setRegistre.remote(self.registre)
            if sync is not True:
                agent.setCopyName.remote(copy_name)
                copy_agent = ray.remote(agent_class).remote(actor_net, value_net, q_net, n_states, n_actions, config,
                                                            sync)
                self.registre.addAgent.remote(copy_name, copy_agent)
                copy_agent.setRegistre.remote(self.registre)
        retref = self.registre.getAllAgent.remote(name)
        return ray.get(retref)

    def getAgent(self, name):
        for i in range(100):
            agent =ray.get(self.registre.getAgent.remote(name))
            if agent != None:
                return agent
            time.sleep(1)
        raise ValueError(name + " agent not found ,please check that the name is correct")

    def startAllRunner(self, runners):
        results =[]
        for runner in runners:
            ref = runner.run.remote()
            results.append(ref)
        ray.get(results)