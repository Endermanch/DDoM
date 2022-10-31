from PyQt5.QtCore import QObject, QMetaMethod, QThread


def getSignal(qobject: QObject, signal_name: str):
    meta_object = qobject.metaObject()

    for i in range(meta_object.methodCount()):
        meta_method = meta_object.method(i)

        if not meta_method.isValid():
            continue

        if meta_method.methodType() == QMetaMethod.Signal and \
                meta_method.name() == signal_name:
            return meta_method

    return None


def create_thread(worker, prefunctions, thrfunction, endfunctions):
    """Create a thread with basic signal connections.

       :return: Pointer to the created thread.
    """

    # Create thread
    thread = QThread()

    # Move worker to thread (POSITIONING is important)
    worker.moveToThread(thread)

    # Clean up worker and quit the thread
    worker.finished.connect(worker.deleteLater)
    worker.finished.connect(thread.quit)

    # Connect functions to be start after thread executes
    for function in endfunctions:
        worker.finished.connect(function)

    # Connect functions to be started parallel to the thread
    for function in prefunctions:
        thread.started.connect(function)

    # Connect main worker function
    thread.started.connect(getattr(worker, thrfunction))

    # Clean up thread
    thread.finished.connect(thread.deleteLater)

    return thread
