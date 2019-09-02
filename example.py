from mikro import Mikro, main


@Mikro.service("/random")
def random_number(*args):
    return Response(HTTPStatus.OK, "4")


if __name__ == "__main__":
    main()
