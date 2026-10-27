package fixtures.negative;

public class NotDurable {
    // A builder, not a call: a pattern on WebClient's methods matches this and files a bean factory as an outbound call.
    void factory() {
        org.springframework.web.reactive.function.client.WebClient.builder();
    }
}

// In-process Camel wiring; reading it as a service boundary reports internal plumbing
// as the dependency graph.
class InternalOnly extends RouteBuilder {
    @Override
    public void configure() {
        from("direct:step-one").to("direct:step-two").to("seda:async").to("mock:result");
        from("seda:queue").to("log:audit").to("bean:handler");
    }
}

// **A poller wearing a subscriber's clothes.** Bank of Anthos's LedgerReader is documented as
// "listens for and reacts to incoming transactions", exposes startWithCallback, and is
// registered exactly the way a subscription is registered — and it is a thread that sleeps
// 100ms and re-queries a table. That estate has no broker of any kind: a rule that read this
// registration as a message receive would put a message edge on a system where no message
// exists, and the edge would look as sound as a real one.
//
// This guards any receive rule:
// it is inert until a rule tries to match it,
// and that is the point.
interface LedgerReaderCallback {
    void processTransaction(String transaction);
}

class PollingNotSubscribing {
    private LedgerReaderCallback callback;

    public void startWithCallback(LedgerReaderCallback cb) {
        this.callback = cb;
    }
}

class PollingRegistration {
    void wire(PollingNotSubscribing reader) {
        reader.startWithCallback(this::handle);
    }

    void handle(String transaction) {
    }
}
