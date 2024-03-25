import time
from celery.exceptions import Ignore

from django.core.mail import send_mail

from megano.celery import app
from services.services import PaymentService, ImportProductService


@app.task
def pay_order(order_id: int, card: str):
    """
    Таск на оплату
    """

    PaymentService(order_id, card).get_payment()


@app.task(track_started=True, bind=True)
def import_product(self, file_data: list, name: str, email: str) -> None:
    """
    Таск на импорт продуктов, запущенный из админки
    """

    time.sleep(10)

    result = ImportProductService().import_product(
        file_data=file_data,
        file_name=name,
    )

    message = result[0]
    bad_result = result[1]

    if bad_result:
        message = result[0] + str(result[1][0])

    send_mail(
        subject=f'Импорт файла {name}',
        message=message,
        from_email=None,
        recipient_list=[email],
    )

    if bad_result:
        self.update_state(state='FAILURE')

        raise Ignore()


@app.task(track_started=True, bind=True)
def import_product_from_command(self, file_data: list, name: str, email: str, file_path: str) -> None:
    """
    Таск на импорт продуктов, запущенный командой в консоли
    """

    time.sleep(10)

    result = ImportProductService().import_product(
        file_data=file_data,
        file_name=name,
        file_path=file_path,
    )

    message = result[0]
    bad_result = result[1]

    if bad_result:
        message = result[0] + str(result[1][0])

    send_mail(
        subject=f'Импорт файла {name}',
        message=message,
        from_email=None,
        recipient_list=[email],
    )

    if bad_result:
        self.update_state(state='FAILURE')

        raise Ignore()
