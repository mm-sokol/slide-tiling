import yaml
from pathlib import Path


def make_dirs(root, name, classes):

    datapaths = {}
    dataroot = Path(root, name)
    for split in ["labels", "images"]:
        for subsplit in ["train", "test", "valid"]:
            datapath = dataroot / Path(split, subsplit)
            datapath.mkdir(parents=True, exist_ok=True)

            if split == "images":
                datapaths[subsplit] = datapath

    dataset_info = {
        "path": dataroot,
        **datapaths,
        "names": {i: classname for i, classname in enumerate(classes)},
    }

    with open(dataroot / f"{name}.yaml", "w") as config:
        yaml.dump(dataset_info, config, default_flow_style=False)


# path: coco # dataset root dir
# train: train2017.txt # train images (relative to 'path') 118287 images
# val: val2017.txt # val images (relative to 'path') 5000 images
# test: test-dev2017.txt # 20288 of 40670 images, submit to https://competitions.codalab.org/competitions/20794

# # Classes
# names:
#   0: person
#   1: bicycle
#   2: car
#   3: motorcycle
#   4: airplane
