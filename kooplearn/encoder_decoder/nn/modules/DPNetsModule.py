from lightning import LightningModule


class DPNetsModule(LightningModule):
    def __init__(self, model_class, model_hyperparameters,
                 optimizer_fn, optimizer_hyperparameters, loss_fn,
                 scheduler_fn=None, scheduler_hyperparameters=None, scheduler_config=None,
                 model_class_2=None, model_hyperparameters_2=None,
                 ):
        super().__init__()
        for k, v in model_hyperparameters.items():
            self.hparams[k] = v
        for k, v in model_hyperparameters_2.items():
            self.hparams[f'model_2_{k}'] = v
        for k, v in optimizer_hyperparameters.items():
            self.hparams[f'optim_{k}'] = v
        for k, v in scheduler_hyperparameters.items():
            self.hparams[f'sched_{k}'] = v
        for k, v in scheduler_config.items():
            self.hparams[f'sched_{k}'] = v
        self.save_hyperparameters()
        self.model = model_class(**model_hyperparameters)
        # If model_class_2 is None, the model_2 is the same as model (with shared weights)
        if model_class_2 is not None:
            self.model_2 = model_class_2(**model_hyperparameters_2)
        else:
            self.model_2 = self.model
        self.optimizer_fn = optimizer_fn
        self.scheduler_fn = scheduler_fn
        self.optimizer_hyperparameters = optimizer_hyperparameters
        self.scheduler_hyperparameters = scheduler_hyperparameters
        self.scheduler_config = scheduler_config
        self.loss_fn = loss_fn

    def configure_optimizers(self):
        optimizer = self.optimizer_fn(self.parameters(), **self.optimizer_hyperparameters)
        if self.scheduler_fn is not None:
            scheduler = self.scheduler_fn(optimizer, **self.scheduler_hyperparameters)
            lr_scheduler_config = self.scheduler_config.copy()
            lr_scheduler_config['scheduler'] = scheduler
            return [optimizer], [lr_scheduler_config]
        return optimizer

    def training_step(self, train_batch, batch_idx):
        outputs = self.base_step(train_batch, batch_idx)
        return outputs

    def validation_step(self, valid_batch, batch_idx):
        outputs = self.base_step(valid_batch, batch_idx)
        return outputs

    def forward(self, batch):
        # dimensions convention (..., channels, temporal_dim)
        return self.model(batch)

    def base_step(self, batch, batch_idx):
        # dimensions convention (..., channels, temporal_dim)
        data_x = {'x_value': batch['x_value']}
        data_y = {'x_value': batch['y_value']}
        model_output_x = self.model(data_x)
        x_encoded = model_output_x['x_encoded']
        # Note that model_2 is the same as model in case we have not defined a second model
        model_output_y = self.model_2(data_y)
        y_encoded = model_output_y['x_encoded']
        loss = self.loss_fn(x_encoded, y_encoded)
        outputs = {
            'loss': loss,
        }
        return outputs
    