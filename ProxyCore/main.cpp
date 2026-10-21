#include "proxy.h"

int main() {
    ProxyServer proxy(8080);
    proxy.start();
    return 0;
}
