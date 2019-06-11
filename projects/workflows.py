import os

from neo4j import GraphDatabase, basic_auth

from datasets.models import Dataset, NSTemplate, MembershipNSTemplate
from users.models import Role, Affiliation
from workflows.models import WorkflowNeo4j
from workflows.workflow_neo4j import create_workflow_from_template, delete_workflow_by_uuid
from .models import MembershipProjectWorkflow, Project

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


def create_base_project_workflows(project_uuid, user):
    """
    Create base project workflows from dataset associations
    for each dataset
      for each template
        new workflow object in django
        new graph: GraphID=uuid of django object
        insert table MembershipProjectWorkflow
          - ProjectID
          - GraphID
          - TemplateID
          - WorkflowNeo4jID
    """
    # create base workflow graphs for new datasets
    affiliation_list = Project.objects.values_list('affiliations__uuid', flat=True).filter(
        uuid=project_uuid
    )
    ds_list = Project.objects.values_list('datasets__uuid', flat=True).filter(
        uuid=project_uuid
    )
    for affiliation_uuid in affiliation_list:
        for ds_uuid in ds_list:
            tplt_list = NSTemplate.objects.values_list('uuid', 'graphml_definition').filter(
                uuid__in=MembershipNSTemplate.objects.values_list('template__uuid').filter(
                    dataset__uuid=ds_uuid
                )
            )
            # check for project, affiliation, dataset, template membership inclusion
            # if it does not exist, create a new base workflow
            for tplt_uuid, graphml_file in tplt_list:
                if not MembershipProjectWorkflow.objects.filter(
                        project__uuid=project_uuid,
                        affiliation__uuid=affiliation_uuid,
                        dataset__uuid=ds_uuid,
                        template__uuid=tplt_uuid,
                ).exists():
                    wf_name = str(Dataset.objects.get(uuid=ds_uuid).name) + ' (' \
                              + str(NSTemplate.objects.get(uuid=tplt_uuid).type) + ')'
                    nw_neo4j = WorkflowNeo4j.objects.create(
                        name=wf_name,
                        affiliation=Affiliation.objects.get(uuid=affiliation_uuid),
                        description=NSTemplate.objects.get(uuid=tplt_uuid).description,
                        dataset=Dataset.objects.get(uuid=ds_uuid),
                        template=NSTemplate.objects.get(uuid=tplt_uuid),
                        created_by=user,
                        modified_by=user,
                    )
                    # create workflow django object
                    workflow_uuid = nw_neo4j.uuid
                    if create_workflow_from_template(graphml_file, workflow_uuid):
                        nw_neo4j.loaded_in_neo4j = True
                        nw_neo4j.save()
                        set_neo4j_workflow_roles(workflow_uuid)
                    # create project / workflow relationship
                    MembershipProjectWorkflow.objects.create(
                        project=Project.objects.get(uuid=project_uuid),
                        affiliation=Affiliation.objects.get(uuid=affiliation_uuid),
                        dataset=Dataset.objects.get(uuid=ds_uuid),
                        template=NSTemplate.objects.get(uuid=tplt_uuid),
                        workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
                        is_generated=True,
                    )
    # delete workflow graphs for datasets removed from project
    # check by affiliation
    wf_affiliation_list = MembershipProjectWorkflow.objects.values_list('affiliation__uuid', flat=True).filter(
        project__uuid=project_uuid,
    ).distinct()
    project_affiliation_list = Project.objects.values_list('affiliations__uuid', flat=True).filter(
        uuid=project_uuid
    )
    for wf_affiliation_uuid in wf_affiliation_list:
        if wf_affiliation_uuid not in project_affiliation_list:
            wf_remove_list = MembershipProjectWorkflow.objects.values_list('workflow__uuid', flat=True).filter(
                project__uuid=project_uuid,
                affiliation__uuid=wf_affiliation_uuid,
            )
            for wf_remove_uuid in wf_remove_list:
                # remove workflow
                delete_workflow_by_uuid(wf_remove_uuid)
                # remove django object
                WorkflowNeo4j.objects.filter(uuid=wf_remove_uuid).delete()
                # remove relationship
                MembershipProjectWorkflow.objects.filter(workflow__uuid=wf_remove_uuid).delete()
    # check by dataset
    wf_ds_list = MembershipProjectWorkflow.objects.values_list('dataset__uuid', flat=True).filter(
        project__uuid=project_uuid,
    )
    for wf_ds_uuid in wf_ds_list:
        if wf_ds_uuid not in ds_list:
            wf_list = MembershipProjectWorkflow.objects.values_list('workflow__uuid', flat=True).filter(
                project__uuid=project_uuid,
                dataset__uuid=wf_ds_uuid,
            )
            for wf_uuid in wf_list:
                # delete the workflow in neo4j
                delete_workflow_by_uuid(wf_uuid)
                # delete wth workflow django object
                WorkflowNeo4j.objects.filter(
                    uuid=wf_uuid
                ).delete()
                # delete the project / workflow relationship
                MembershipProjectWorkflow.objects.filter(
                    project__uuid=project_uuid,
                    dataset__uuid=wf_ds_uuid,
                    workflow__uuid=wf_uuid
                ).delete()


def set_neo4j_workflow_roles(workflow_uuid):
    wf_obj = WorkflowNeo4j.objects.get(uuid=workflow_uuid)
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + \
                "' AND n.SAFEType in ['common-set', 'template-user-set', 'None'] RETURN path"
    results = db.run(statement).graph()
    db.close()
    for node in results.nodes:
        for key in node.keys():
            if key == 'Role':
                roles = str(node[key])
                for role in roles.split(','):
                    if role == 'None':
                        pass
                    elif role == 'PI':
                        if not wf_obj.roles.filter(id=int(getattr(Role, 'PI_ADMIN'))).exists():
                            wf_obj.roles.add(int(getattr(Role, 'PI_ADMIN')))
                            print("Adding role " + str(Role.objects.get(id=int(getattr(Role, 'PI_ADMIN')))))
                        if not wf_obj.roles.filter(id=int(getattr(Role, 'PI_MEMBER'))).exists():
                            wf_obj.roles.add(int(getattr(Role, 'PI_MEMBER')))
                    else:
                        if not wf_obj.roles.filter(id=int(getattr(Role, role))).exists():
                            wf_obj.roles.add(int(getattr(Role, role)))
                            print("Adding role " + str(Role.objects.get(id=int(getattr(Role, role)))))
    wf_obj.save()


def generate_neo4j_user_workflows(project_obj, user_obj):
    print('Hello')
    # get roles from project and match to user
    # get workflows from project and match to user by affiliation
    # for each workflow, for each role, generate appropriate child nodes
    # update user workflow table for generation and completeness
    pass
