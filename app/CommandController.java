import java.io.IOException;
import java.net.InetAddress;

public class CommandController {
    public boolean isReachable(String host) throws IOException {
        InetAddress address = InetAddress.getByName(host);
        return address.isReachable(2000);
    }
}
