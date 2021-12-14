def register_all():
    # NOTE: You must make sure your object gets imported in this
    # function in order for it to be registered by services that may
    # need to receive it via RPC.
    __import__('convertor.objects.task')
