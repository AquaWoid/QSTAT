from pydantic import BaseModel


class topic_model_settings(BaseModel):
    n_neighbours: int
    n_components: int
    min_cluster_size: int
    min_samples: int    

