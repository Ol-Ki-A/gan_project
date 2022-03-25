# -*- coding: utf-8 -*-
"""weight_norm.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uGaEZGFQmGsFNH32iaMP20CUcDN6z4Xk
"""

import torch
import torchvision
from torchvision import transforms
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import torch.optim as optim
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision.transforms import ToTensor

import os
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as tt
import torch
import torch.nn as nn
import cv2
from tqdm.notebook import tqdm
import torch.nn.functional as F
from torchvision.utils import save_image
from torchvision.utils import make_grid
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

training_data = torchvision.datasets.MNIST(
    root='./data',
    train=True,
    download=True,
    transform=transforms.Compose ([ 
        transforms.ToTensor () 
        ])
)

test_data = torchvision.datasets.MNIST(
    root='./data',
    train=False,
    download=True,
    transform=transforms.Compose ([ 
        transforms.ToTensor () 
        ])
)

batch_size = 100

batch_size_test = 100

train_loader = torch.utils.data.DataLoader(training_data, batch_size= batch_size, shuffle=True, num_workers=2)

test_loader = torch.utils.data.DataLoader(test_data, batch_size= batch_size_test, shuffle=False, num_workers=2)

"""discriminator = nn.Sequential(
    #  1 x 28 x 28

    nn.Conv2d(1, 64, kernel_size=2, stride=2, padding=1, bias=False),
    nn.BatchNorm2d(64),
    nn.LeakyReLU(0.2, inplace=True),

    nn.Conv2d(64, 128, kernel_size=2, stride=2, padding=1, bias=False),
    nn.BatchNorm2d(128),
    nn.LeakyReLU(0.2, inplace=True),

    nn.Conv2d(128, 256, kernel_size=2, stride=2, padding=1, bias=False),
    nn.BatchNorm2d(256),
    nn.LeakyReLU(0.2, inplace=True),

    nn.Conv2d(256, 512, kernel_size=2, stride=2, padding=1, bias=False),
    nn.BatchNorm2d(512),
    nn.LeakyReLU(0.2, inplace=True),

    nn.Conv2d(512, 1, kernel_size=3, stride=1, padding=0, bias=False),

    nn.Flatten(),
    nn.Sigmoid())"""

from torch.nn.utils import weight_norm

discriminator = nn.Sequential(
    #  1 x 28 x 28
    (nn.Linear(784, 1024)),
    nn.Dropout(p=0.3),
    nn.LeakyReLU(0.2, inplace=True),
    (nn.Linear(1024, 512)),
    nn.Dropout(p=0.3),
    nn.LeakyReLU(0.2, inplace=True),
    (nn.Linear(512, 128)),
    nn.Dropout(p=0.3),
    nn.LeakyReLU(0.2, inplace=True),
    (nn.Linear(128, 1)),
    nn.Flatten(),
    nn.Sigmoid())

latent_size = 100
generator = nn.Sequential(       
        weight_norm(nn.Linear(latent_size, 128)),
        nn.LeakyReLU(0.2, inplace=True),
        (nn.Linear(128, 256)),
        nn.LeakyReLU(0.2, inplace=True),
        weight_norm(nn.Linear(256, 512)),
        nn.LeakyReLU(0.2, inplace=True),
        (nn.Linear(512, 784)),
        nn.BatchNorm1d(784),
        nn.Sigmoid()
)

latent_size = 100

"""generator = nn.Sequential(

    nn.ConvTranspose2d(latent_size, 80, kernel_size=2, stride = 2),
    nn.BatchNorm2d(80),
    nn.ReLU(),
   
    nn.ConvTranspose2d(80, 64, kernel_size=2, stride=4),
    nn.BatchNorm2d(64),
    nn.ReLU(),

    nn.ConvTranspose2d(64, 32, kernel_size=2, stride=5),
    nn.BatchNorm2d(32),
    nn.ReLU(),

    nn.ConvTranspose2d(32, 1, kernel_size=2, stride=1),
    nn.ReLU()
)

#1 x 28 x 28
"""

opt1 = torch.optim.Adam(discriminator.parameters(), lr=1e-4)

opt2 = torch.optim.Adam(generator.parameters(), lr=1e-4)

BCE_loss1 = torch.nn.MSELoss()
BCE_loss2 = torch.nn.MSELoss()

device = torch.device("cuda")

discriminator.to(device)
generator.to(device)

from tqdm.notebook import tqdm

from torch.autograd import Variable

losses_generator = []
losses_discriminator = []
real_score = []
fake_score = []
real_scores = []
fake_scores = []
epochs = 101
losses_g = []
losses_d = []
for epoch in range(epochs):
  loss_d_per_epoch = []
  loss_g_per_epoch = []
  real_score_per_epoch = []
  fake_score_per_epoch = []
  for real_images, _ in tqdm(train_loader):
    opt1.zero_grad()
    real_images = real_images.to(device)
    real_images = real_images.view(-1, 784)
    real_preds = discriminator(real_images)
    #присвоим реальному изображению метку класса 1
    real_targets = torch.ones(real_images.size(0), 1, device=device) #- torch.full((real_images.size(0), 1), np.random.uniform(0,0.05), device=device)  
    #учим дисриминатор предсказывать эту метку класса
    real_loss = BCE_loss1(real_preds, real_targets)
    #берем латентный вектор
    latent = torch.randn(batch_size, latent_size, device=device)
    #генерируем изображение
    fake_images = generator(latent)
    #присваимваем метку класса 0
    fake_targets = torch.zeros(fake_images.size(0), 1, device=device) #+ torch.full((real_images.size(0), 1), np.random.uniform(0,0.05), device=device)
    #подвем в дискриминатор, считаем лосс
    fake_preds = discriminator(fake_images)
    fake_loss = BCE_loss2(fake_preds, fake_targets)
    #считаем скор и делаем шаг
    real_score_per_epoch.append(torch.mean(real_preds).item())
    fake_score_per_epoch.append(torch.mean(fake_preds).item())
    loss_d = real_loss + fake_loss
    loss_d.backward()
    opt1.step()
    loss_d_per_epoch.append(loss_d.item())
    #обучим генератор
    opt2.zero_grad()
        
      #генерируем изображение
    latent = torch.randn(batch_size, latent_size, device=device)
    fake_images = generator(latent)
        
    #подаем изображение дискриминатору 
    preds = discriminator(fake_images)
    targets = torch.ones(batch_size, 1, device=device)
    #считаем лосс генератора 
    loss_g = BCE_loss2(preds, targets)
    # делаем шаг
    loss_g.backward()
    opt2.step()
    loss_g_per_epoch.append(loss_g.item())
  if (epoch % 5 == 0):  
    torch.save(generator, "model_gen" + str(epoch + 900) + ".zip")
    torch.save(discriminator, "model_dis" + str(epoch + 900) + ".zip")
  print(f'loss generator on {epoch + 600} = {np.mean(loss_g_per_epoch)}')
  print(f'loss discriminator on {epoch + 600} = {np.mean(loss_d_per_epoch)}')
  print(f'real scores on {epoch + 600} = {np.mean(real_score_per_epoch)}')
  print(f'fake scores on {epoch + 600} = {np.mean(fake_score_per_epoch)}')
  losses_g.append(np.mean(loss_g_per_epoch))
  losses_d.append(np.mean(loss_d_per_epoch))
  real_scores.append(np.mean(real_score_per_epoch))
  fake_scores.append(np.mean(fake_score_per_epoch))

discriminator = torch.load("model_dis1000.zip")
generator = torch.load("model_gen1000.zip")

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

discriminator = torch.load("model_dis110.zip")
generator = torch.load("model_gen110.zip")

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

latent_size = 100
batch_size = 100
image = []
device = "cuda"
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

image = []
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

plt.figure(figsize=(15, 6))
plt.plot(losses_d, '-')
plt.plot(losses_g, '-')
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['Discriminator', 'Generator'])
plt.title('Losses');

image = []
for i in range(64):
  latent = torch.randn(batch_size, latent_size, device=device)
  fake_image = generator(latent)
  fake_image = fake_image.view(fake_image.size(0), 1, 28, 28)
  #fake_image = fake_image.cpu().detach().numpy() 
  image.append(fake_image[0].cpu())
#image = torch.FloatTensor(image) 
print(fake_image.shape)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
ax.imshow(make_grid(image, nrow=8).permute(1, 2, 0))

+latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

latent = torch.randn(batch_size, latent_size, device=device)
fake_images = generator(latent)
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xticks([]); ax.set_yticks([])
fake_images = fake_images.view(fake_images.size(0), 1, 28, 28)
fake_images = fake_images.cpu().detach().numpy()
ax.imshow(fake_images[0][0])

discriminator = torch.load("model_dis140.zip")
generator = torch.load("model_gen140.zip")