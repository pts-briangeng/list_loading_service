from tests.builders.elastic_search_builders import (create_response_builder, status_response_builder,
                                                    delete_response_builder)

ESCreateResponseBuilder = create_response_builder.CreateListResponseJsonBuilder
ESDeleteResponseBuilder = delete_response_builder.DeleteListResponseJsonBuilder
ESStatusResponseBuilder = status_response_builder.ListStatusResponseJsonBuilder
