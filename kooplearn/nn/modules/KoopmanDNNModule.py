import torch.functional as F
from lightning import LightningModule

from kooplearn.data.utils.TimeseriesDataset import TimeseriesDataset


class KoopmanDNNModule(LightningModule):
    def __init__(self, model_class, model_hyperparameters, optimizer_fn, optimizer_hyperparameters, loss_fn,
                 koopman_estimator=None, koopman_estimator_hyperparameters=None,
                 decoder=None, decoder_hyperparameters=None,
                 scheduler_fn=None, scheduler_hyperparameters=None, scheduler_config=None):
        super().__init__()
        for k, v in model_hyperparameters.items():
            self.hparamsxz[k] = v
        for k, v in optimizer_hyperparameters.items():
            self.hparams[f'optim_{k}'] = v
        for k, v in koopman_estimator_hyperparameters.items():
            self.hparams[f'koop_{k}'] = v
        for k, v in decoder_hyperparameters.items():
            self.hparams[f'dec_{k}'] = v
        for k, v in scheduler_hyperparameters.items():
            self.hparams[f'sched_{k}'] = v
        for k, v in scheduler_config.items():
            self.hparams[f'sched_{k}'] = v
        self.save_hyperparameters()
        self.model = model_class(**model_hyperparameters)
        self.optimizer_fn = optimizer_fn
        self.koopman_estimator = koopman_estimator
        self.decoder = decoder
        self.scheduler_fn = scheduler_fn
        self.optimizer_hyperparameters = optimizer_hyperparameters
        self.scheduler_hyperparameters = scheduler_hyperparameters
        self.scheduler_config = scheduler_config
        self.loss_fn = loss_fn

    # @classmethod
    # def from_timeseries_dataset(cls, model_class, model_hyperparameters, dataset: TimeseriesDataset,
    #                             optimizer_fn, optimizer_hyperparameters,
    #                             scheduler_fn, scheduler_hyperparameters, scheduler_config, loss_fn,
    #                             koopman_estimator, koopman_estimator_hyperparameters,
    #                             decoder, decoder_hyperparameters,
    #                             ):
    #     model_kwargs_from_dataset = model_class.time_series_dataset_to_model_kwargs(dataset)
    #     model_hyperparameters.update(model_kwargs_from_dataset)
    #     optimizer_kwargs_from_dataset = model_class.time_series_dataset_to_optimizer_kwargs(dataset)
    #     optimizer_hyperparameters.update(optimizer_kwargs_from_dataset)
    #     scheduler_kwargs_from_dataset = model_class.time_series_dataset_to_scheduler_kwargs(dataset)
    #     scheduler_hyperparameters.update(scheduler_kwargs_from_dataset)
    #     koopman_estimator_kwargs_from_dataset = model_class.time_series_dataset_to_koopman_estimator_kwargs(dataset)
    #     koopman_estimator_hyperparameters.update(koopman_estimator_kwargs_from_dataset)
    #     decoder_kwargs_from_dataset = model_class.time_series_dataset_to_decoder_kwargs(dataset)
    #     decoder_hyperparameters.update(decoder_kwargs_from_dataset)
    #     return cls(model_class=model_class, model_hyperparameters=model_hyperparameters,
    #                optimizer_fn=optimizer_fn, optimizer_hyperparameters=optimizer_hyperparameters,
    #                scheduler_fn=scheduler_fn, scheduler_hyperparameters=scheduler_hyperparameters,
    #                scheduler_config=scheduler_config, loss_fn=loss_fn,
    #                koopman_estimator=koopman_estimator,
    #                koopman_estimator_hyperparameters=koopman_estimator_hyperparameters,
    #                decoder=decoder, decoder_hyperparameters=decoder_hyperparameters,
    #                )

    def configure_optimizers(self):
        optimizer = self.optimizer_fn(self.parameters(), **self.optimizer_hyperparameters)
        if self.scheduler_fn is not None:
            scheduler = self.scheduler_fn(optimizer, **self.scheduler_hyperparameters)
            lr_scheduler_config = self.scheduler_config.copy()
            lr_scheduler_config['scheduler'] = scheduler
            return [optimizer], [lr_scheduler_config]
        return optimizer

    def forward(self, batch):
        # dimensions convention (batch_size, channels, temporal_dim)
        return self.model(batch)

    def base_step(self, batch, batch_idx):
        raise NotImplementedError
        # # train and fit on batch
        # mask_out_of_series_left = batch['mask_out_of_series_left']
        # mask_out_of_series_right = batch['mask_out_of_series_right']
        # y_true = batch['y_value']
        # model_output = self(batch)
        # x_encoded = model_output['x_encoded']
        # self.koopman_estimator.fit(x_encoded, y_encoded)
        # y_encoded = self.koopman_estimator(x_encoded)
        # y_pred = self.decoder(y_encoded)
        # mask_out_of_series = mask_out_of_series_left + mask_out_of_series_right
        # mask_in_series = ~mask_out_of_series
        # y_pred = y_pred * mask_in_series
        # y_true = y_true * mask_in_series
        # loss = self.loss_fn(y_pred, y_true)
        # outputs = {
        #     'loss': loss,
        #     'y_true': y_true,
        #     'y_pred': y_pred,
        #     'mask_out_of_series': mask_out_of_series
        # }
        # return outputs

    def training_step(self, train_batch, batch_idx):
        outputs = self.base_step(train_batch, batch_idx)
        return outputs

    def validation_step(self, valid_batch, batch_idx):
        outputs = self.base_step(valid_batch, batch_idx)
        return outputs

    def test_step(self, test_batch, batch_idx):
        outputs = self.base_step(test_batch, batch_idx)
        return outputs

    # def predict_step(self, batch, batch_idx, dataloader_idx=0):
    #     outputs = self.base_step(batch, batch_idx)
    #     return outputs
