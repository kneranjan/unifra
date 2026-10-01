import docker


#client  is the docker connection and results is the list of the containers we found


def discover_containers() -> list[dict]:
  client = docker.from_env()

  results = []
  #all = True includes stopped containers

  for c in client.containers.list(all=True):
    results.append({
        "container_id" : c.short_id,
        "name" : c.name,
        "image" : c.attrs["Config"]["Image"],
        "state" : c.status,
    })

  return results