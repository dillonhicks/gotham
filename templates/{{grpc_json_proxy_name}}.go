package main
import (
        "flag"
        "net/http"

        "github.com/golang/glog"
        "golang.org/x/net/context"
        "github.com/grpc-ecosystem/grpc-gateway/runtime"
        "google.golang.org/grpc"
        gw "{{package.name}}"
)

var (
        server = flag.String("service_endpint", "localhost:8080", "grpc service endpoint of {{package.name}}")
        port = flag.String("port", ":9090", "The port on which to run this proxy")
)


func run() error {
        ctx := context.Background()
        ctx, cancel := context.WithCancel(ctx)
        defer cancel()

        mux := runtime.NewServeMux()
        opts := []grpc.DialOption{grpc.WithInsecure()}
{% for service_name in service_names %}
        glog.Info("{{package.name.title()}} - Registering service {{service_name}}")
        if err := gw.Register{{service_name}}HandlerFromEndpoint(ctx, mux, *server, opts); err != nil {
                glog.Warning("Error registering service {{service_name}}")
                return err
        }
{% endfor %}
        glog.Info("{{package.name.title()}} grpc proxy server will proxy requests to ", *server)
        glog.Info("{{package.name.title()}} grpc proxy server starting to listen on ", *port)
        http.ListenAndServe(*port, mux)
        return nil
}


func main() {
        flag.Parse()
        defer glog.Flush()

        if err := run(); err != nil {
                glog.Fatal(err)
        }
}
