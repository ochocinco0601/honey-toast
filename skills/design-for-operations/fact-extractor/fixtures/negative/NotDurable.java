package fixtures.negative;

public class NotDurable {
    // A builder, not a call. The documented reason the WebClient patterns were cleared.
    void factory() {
        org.springframework.web.reactive.function.client.WebClient.builder();
    }
}

// In-process Camel wiring. 68 of these on the reference integration estate; reading them as
// service boundaries would report internal plumbing as the estate's dependency graph.
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
// Placed here BEFORE the receive rules it guards were written, because the whole
// occasion for those rules was a message seam that failed silently. This one is inert until a
// rule tries to match it, and that is the point.
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
