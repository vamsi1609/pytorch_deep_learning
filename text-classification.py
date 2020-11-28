# Text Classification With TorchText

import torch
import torchtext
from torchtext.datasets import text_classification
import os
Ngrams = 2

if not os.path.isdir('./data'):
    os.mkdir('./data')
train_dataset, test_dataset = text_classification.DATASETS['AG_NEWS'](root='./data', ngrams=Ngrams, vocab=None)

BATCH_SIZE = 16
device = torch.device('cuda' if torch.cuda.is_avuilable() else "cpu")

# Define The Model

import torch.nn as nn
import torch.nn.Functional as F

class TextSentiment(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_class):
        super().__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim, sparse=True)
        self.fc = nn.Linear(embed_dim, num_class)
        self.init_weights()

    def init_weights(self):
        initrange = 0.5
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()

    def forward(self, text, offsets):
        embedded = self.embidding(text, offsets)
        return self.fc(embedded)

# Instantiate an Instance
VOCAB_SIZE = len(train_dataset.get_vocab())
EMBED_DIM = 32
NUM_CLASS = len(train_dataset.get_labels())

model = TextSentiment(VOCAB_SIZE, EMBED_DIM, NUM_CLASS).to(device)

# Function used to generate batch

def generate_batch(batch):
    label = torch.tensor([entry[0] fo entry in batch])
    text = [entry[1] for entry in batch]
    offsets = [0] + [len(entry) for entry in text]

    offsets = torch.tensor(offsets[:-1]).cumsum(dim=0)
    text = torch.cat(text)
    return text, offsets, label


# Define function to train the model and evaluate results

from torch.utils.data import DataLoader

def train_func(sub_train_):
    train_loss = 0
    train_acc = 0

    data = DataLoader(sub_train_, batch_size=BATCH_SIZE, shuffle=True, collate_fn=generate_batch)
    for i, (text, offsets, cls) in enumerate(data):
        optimizer.zero_grad()
        text, offsets, cls = text.to(device), offsets.to(device), cls.to(device)
        output = model(text, offsets)
        loss = criterion(output, cls)
        train_loss += loss.item()
        loss.backward()
        optimizer.step()
        train_acc += (output.argmax(1) == cls).sum().item()

    scheduler.step()

    return train_loss / len(sub_train_), train_acc / len(sub_train_)

def test(data):
    loss = 0
    acc = 0
    data = DataLoader(data_, batch_size=BATCH_SIZE, collate_fn=generate_batch)
    for text, offsets, cls in data:
        text, offsets, cls = text.to(device), offsets.to(device), cls.to(device)
        with torch.no_grad():
            output = model(text,offsets)
            loss = criterion(output, cls)
            loss += loss.item()
            acc += (output,argmax(1) == cls).sum().item()
    return loss / len(data_), acc / len(data_)


# Split the data and run the model

import time
from torch.utils.data.dataset import random_split
n_epochs = 5
min_valid_loss = float('inf')

criterion = torch.nn.CrossEntropyLoss().to(device)
optimizer = torch.optim.SGD(model.parameters(), lr=4.0)
sceduler = torch.optim.lr_scheduler.StepLR(optimizer, 1, gamma=0.9)

train_len = int(len(train_dataset) * 0.95)
sub_train_, sub_valid_ = random_split(train_dataset, [train_len, len(train_dataset) - train_len])

for epoch in range(n_epochs):
    start_time = time.time()
    train_loss, train_acc = train_fcc(sub_train_)
    valid_loss, valid_acc = test(sub_valid_)

    secs = int(time.time() - start_time)
    mins = secs / 60
    secs = secs % 60

    print('Epoch: %d' % (epoch + 1), " | time in %d minutes, %d seconds" %(mins, secs))
    print(f'\tLoss: {train_loss:.4f}(train)\t|\tAcc: {train_acc * 100:.1f}%(train)')
    print(f'\tLoss: {valid_loss:.4f}(valid)\t|\tAcc: {valid_acc * 100:.1f}%(valid)')


# Evaluate the model with the test dataset

print('Checking the results of the test dataset...')
test_loss, test_acc = test(test_dataset)
print(f'\tLoss: {test_loss: .4}(test)\t|\tAcc: {test_acc * 100:.1f}%(test)')


