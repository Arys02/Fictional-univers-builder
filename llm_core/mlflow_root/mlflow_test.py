import mlflow

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)

    for epoch in range(1, 10):
        loss = 1.0 / (epoch + 1)
        mlflow.log_metric("loss", loss, step=epoch)