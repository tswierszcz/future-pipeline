package main

deny contains msg if {
  input.kind == "Deployment"
  c := input.spec.template.spec.containers[_]
  not c.resources.limits.cpu
  msg := "Container must define cpu limit"
}

deny contains msg if {
  input.kind == "Deployment"
  c := input.spec.template.spec.containers[_]
  not c.resources.limits.memory
  msg := "Container must define memory limit"
}
