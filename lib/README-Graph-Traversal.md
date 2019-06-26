# Details of workflow graph traversal

## Some background 

- Question: what to do about template-user-set nodes - when can nodes following them that belong to other principals can be traversed? Do we need to know the set-membership of e.g. STAFF? or do we ignore them for traversal by other principals? Ignoring seems ok, except Question 2 below.

- Question: is it even a valid situation to have a condition placed on a template-user-set node? If so, what does it mean to follow the condition? Condition applies if the principal herself is traversing, but what about other principals?

- Resolution: 
  - Non-PI, non-STAFF nodes must always have 'common-set' type
  - PI nodes with 'common-set' type are treated like any other node - a single representative of PI group can attest
  - PI nodes with 'template-user-set' type must be attested by individual PIs
  - STAFF nodes with 'template-user-set' type must be attested by individual staff members
  - Roles can be a list e.g. "STAFF, PI"
  - template-user-set nodes cannot hold conditions or have fan-outs
  - template-user-set are skipped when traversed on behalf of principal roles that don't match their own
  - conditional and regular fan-ins don't mix on the same node

## Algorithms

find_reachable_node_completed_nodes recursively finds all nodes reachable from current (or Start) node
for a given principal role. It returns a list of such nodes.

```
def find_reachable_not_completed_nodes(principalID, principalRole, node, incompleteSet):

  switch(node.Type):
    'Start':
      foreach newNode in query_incident_nodes(node):
        find_reachable_not_completed_nodes(principalID, principalRole, newNode, incompleteSet)
    'Stop':
      return
    'AssertionItem' or 'ConditionalAssertionItem':
      if node.completed: # continue traversal
        if node_conditional(node):
          # if node is conditional, follow one branch based on ParameterValue
          newNode = query_conditional_incident_nodes(node, node.ParameterValue)
          find_reachable_not_completed_nodes(principalID, principalRole, newNode, incompleteSet)
        else:
          # if not conditional, follow the fan-out
          foreach newNode in query_incident_nodes(node):
            find_reachable_not_completed_nodes(principalID, principalRole, newNode, incompleteSet)
        # exit
        return

      if node.Role != principalRole:
        # if template-user-set and role doesn't match our own, keep traversing
        if node.SAFEType == 'template-user-set':
          # can't be conditional, just find the following node and keep going
          # should only be one
          foreach newNode in query_incident_nodes(node):
            find_reachable_not_completed_nodes(principalID, principalRole, newNode, incompleteSet)
        # otherwise we stop on this branch
        return
      else: # role matches our own
        if node.SAFEType == 'common-set':
          # check for fan-in ignoring template-user-set nodes (regardless of Role) and if done,
          # add to the list and exit
          if check_fan_in_complete(node):
            incompleteSet += node
          return
        elif node.SAFEType == 'template-user-set':
          # create a child if necessary with user-set SAFEType
          childNode = merge_child(node, principalID)
          # if child is completed
          if childNode.completed:
            # follow to the next node (fan-out or conditionals not allowed)
            foreach newNode in query_incident_nodes(node):
              find_reachable_not_completed_nodes(principalID, principalRole, newNode, incompleteSet)
          else:
            # if child not completed, check for fan-in,
            # ignoring template-user-set regardless of Role and add to list and exit
            if check_fan_in_complete(childNode):
              incompleteSet += childNode

          return
```
check_fan_in_complete(node) determines if the unconditional or conditional fan-in allows this node to proceed
```
def check_fan_in_complete(node):
  # find the parent fan out node
  parentNode = find_fan_out_parent_node(node)

  # if this node is not completed, descendants definitely not completed
  if not parentNode.completed:
    return false

  # if parent node is conditional, then we could've only reached
  # this node if one branch is complete and therefore parents are complete
  if node_conditional(parentNode):
    return true

  # if parent node is just a fan-out, then need to check every immediate
  # parent of node to see if it is complete (skipping template-user-set nodes)
  else:
    parentsDone = true
    for parent in find_immediate_parent_nodes(node):
      if not parent.completed:
        parentsDone = false
        break
    return parentsDone
```

save_safe_token_and_done saves a token on the node and marks it done:
```
def save_safe_token_and_done(node, token):
  node.SAFEToken = token
  node.completed = True
```
process node from the list returned from find_reachable_not_completed_nodes:
```
def process_node(principalID, principalRole, node):

  if node.Type != 'AssertionItem' AND node.Type != 'ConditionalAssertionItem':
    error
  if node.SAFEType == 'template-user-set':
    error

  if node.Role != principalRole:
    error

  if node.SAFEType == 'user-set':
      parentNode = query_parent(node)
      if node.ID != parentNode.ID + principalID:
        error # not our node


  if node.ParameterTemplate == None:
    save_safe_token_and_done(node, safe_rest_call(node.SAFETemplate))
  else:
    node.ParameterValue = render_choices(node.ParameterTemplate)
    save_safe_token_and_done(node,
      safe_rest_call(node.SAFETemplate,
      node.ParameterTemplate,
      node.ParameterValue)
```
make selection on conditional node:
```
def make_conditional_selection(node, selectionValue):
  node.ParameterValue = selectionValue
  
  for every successor s not selected by selectionValue:
    create link node->s with type isNotSelectedPrerequisiteFor with copied properties
    remove original link node->s of type isPrerequisiteFor
```
Test workflow for completeness. Note that simply finding all incomplete common-set and user-set nodes
is not correct, since some user-set nodes may be preceded by conditional common-set nodes.
Now that marking conditional node complete includes disabling non-selected branches (by setting their
type to isNotSelectedPrerequisiteFor), testing reachability of common-set nodes becomes trivial

```
def is_workflow_complete(graphId, principalID, principalRole):
  if there are no reachable incomplete common-set nodes and
    find_reachable_not_completed_nodes(graphId, principalID, principalRole) returns empty:
    return True
  return False
```

OLD Queries
A (common-set) node N is reachable if any of the following is true
1. There is a path between start node and N that doesn't traverse a conditional node

MATCH p=(n {ID: "Start"}) -[*]-> (m {ID: $nodeId}) WITH p MATCH(m {Type: "ConditionalAssertionItem"}) WHERE NOT m IN nodes(p) RETURN count(p) >0

2. There is a path between start node and N that traverses conditional nodes that either are
incomplete, or if complete, the next neighbor of the conditional node following the selected branch
is on the path

Find paths through filled-in conditional assertion items

match p=(n {ID: "Start"}) -[*]-> (o {Type: "ConditionalAssertionItem"}) -[q:isPrerequisiteFor]-> () -[*0..]-> (m {ID: "ServerTrainingPledge"}) WHERE o.ParameterValue IS NOT NULL AND o.ParameterValue = q.ParameterValue RETURN p

match p=(n {ID: "Start"}) -[*]-> (o {Type: "ConditionalAssertionItem"}) -[q:isPrerequisiteFor]-> () -[*0..]-> (m {ID: "WorkstationSecurityProtocols"}) WHERE o.ParameterValue IS NULL OR o.ParameterValue IS NOT NULL AND o.ParameterValue = q.ParameterValue RETURN count(p)
match p=(n {ID: "Start"}) -[*]-> (o) -[q:isPrerequisiteFor]-> () -[*0..]-> (m {ID: "WorkstationSecurityProtocols"}) WHERE o.Type = "ConditionalAssertionItem" AND (o.ParameterValue IS NULL OR (o.ParameterValue IS NOT NULL AND o.ParameterValue = q.ParameterValue)) RETURN p