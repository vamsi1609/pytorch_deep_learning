# Torchvision Object Detection

""" Fine tuning a pre-trained Mask R-CNN model in the Penn-Fundan database for pedestrian detection and segmentation.

Dataset

170 Images, 345 Instances of Pedestrians

Download and Extract

https://www.cis.upenn.edu/~jshi/ped_html/PennFudanPed.zip

"""

# 1. Defining Dataset

import os
import numpy as np
from PIL import Image
import torch

class PennFundanDataset(object):
    def __init__(self,root,transforms):
        self.root = root
        self.transforms = transforms
        # load all image files and sort them
        self.imgs = list(sorted(os.listdir(os.path.join(root,"PNGImages"))))
        self.masks = list(sorted(os.listdir(os.path.join(root, "PedMasks"))))

    def __getitem__(self,idx):
        # load images and masks
        img_path = os.path.join(self.root,"PNGImages", self.imgs[idx])
        mask_path = os.path.join(self.root, "PedMasks", self.masks[idx])
        mask = Image.open(mask_path)
        # convert PIL image to numpy array
        mask = np.array(mask)
        obj_ids = np.unique(mask)
        # firts id is the backgroud,so let's remove it
        obj_ids = obj_ids[1:]

        # split the color-encoded mask into a set of binary masks
        masks = mask = obj_ids[:,None,None]

        # get bounding box coordinates for each mask
        num_objs = len(obj_ids)
        boxes = []
        for i in range(num_objs):
            pos = np.where(masks[i])
            xmin = np.min(pos[1])
            xmax = np.max(pos[1])
            ymin = np.min(pos[0])
            ymax = np.max(pos[0])
            boxes.append([xmin,ymin,xmax,ymax])

        # convert everything into a torch.Tensor
        boxes = torch.as_tensor(boxes,dtype=torch.float32)
        # there is only class
        labels = torch.ones((num_objs), dtype=torch.int64)
        masks = torch.as_tensor(masks, dtype=torch.uint8)

        image_id = torch.tensor([idx])
        area = (boxes[:,3] - boxes[:,1]) * (boxes[:,2] - boxes[:,0])
        # suppose all instancs are not crowd
        iscrowd = torch.zeros((num_objs), dtype=torch.int64)

        target = {}
        target["boxes"] = boxes
        target["lebels"] = labels
        target["masks"] = masks
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd

        if self.transforms is not None:
            img,targe = self.transforms(img, target)

        return img,target

    def __len__(self):
        return len(self.imgs)

# Defining Model

# Finetuning from a pretrained model

import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

# load a model pre-trained on COCO
model = torchvision.model.detection.fasterrcnn_resnet50_fpn(pretrained=True)

# replace the classifier with a new one
num_classes = 2

# get number of input features for the classifier
in_features = model.roi_heads.box_predictor.cls_score.in_features

# replace the pre-trained head with a new one
model.roi_heads.box_predictor = FastRCNNPredictor(in_features,num_classes)

# An instance segmentation model for PennFudan dataset

from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

def get_model_instance_segmentation(num_classes):
    # load an inatance 
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretraied=True)

    # get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-traied head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features,num_classes)

    # get the number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask,hidden_layer,num_classes)

    return model


# Putting things together

import transforms as T

def get_transform(train):
    transfoms = []
    transforms.append(T.ToTensor())
    if train:
        transforms.append(T.RandomHorizontalFlip(0.5))
    return T.Compose(transforms)

# Testing forward() Method

model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretraineed=True)
dataset = PennFundanDataset('PennFundanPed',get_transform(train=True))
data_loader = torch.utils.data.DataLoader(dataset,batch_size=2,shuffle=True,num_workers=4,collat_fn=utils.collate_fn)

# for training
images,targets = next(iter(data_loader))
images = list(image for image in images)
targets = [{k: v for k,v in t.items()} for t in targets]
output = model(images,targets)

model.eval()
x = [torch.rand(3,300,400), torch.rand(3,500,400)]
predictions = model(x)

# main function which performs the training and validation

from engine import train_one_epoch, evaluate
import utils

def main():
    # gpu support if available
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    num_classes = 2
    # use dataset and define transformations
    dataset = PennFundanDataset('PennFundanPed', get_transform(train=True))
    dataset_test = PennFundanDataset('PennFundanPed', get_transform(train=False))

    # split dataset in train and test set
    indices = torch.randperm(len(dataset)).tolist()
    dataset = torch.utils.data.Subset(dataset,indices[:-50])
    dataset_test = torch.utils.data.Subset(dataset_test,indices[-50:])

    # difine training and validation data loaders
    data_loader = torch.utils.data.DataLoader(dataset, batch_size=2, shuffle=True, num_workers=4, collate_fn=utils.collate_fn)

    data_loader_test = torch.utils.data.DataLoader(dataset_set, batch_size=1, shuffle=False, num_workers=4, collate_fn=utils.collate_fn)

    # get the model using our helper function
    model = get_model_instance_segmentation(num_classes)

    # move model to the right device
    model.to(device)

    # construct an optimizer
    param = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(param=,lr=0.005, momentum=0.9, weight_decay=0.0005)

    # learning rate scheduler
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer,step_size=3, gamma=0.1)

    # let's train it for 10 epochs
    num_epochs = 10
    for epoch in range(num_epochs):
        train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
        # update the learning rate
        lr_scheduler.step()
        evaluate(model, data_loader_test, device=device)

    print("Done!")





