// Negative control - constructs that must NOT be read as emission sites.
// A match here is a regression in the emission rules' receiver binding.

class NotEmission {

    void notLogging() {
        // An `error` method on something that is not a logger. An unbound receiver,
        // `$X.error(...)`, matches all of these, and each one reads on a fact base as a
        // place the system emits something.
        validationResult.error("field is required");
        responseBuilder.error(400);
        parser.warn("deprecated syntax");

        // `info` on a domain object, same shape, same reason.
        buildReport.info("nothing to do");

        // A builder with a `register` step on a class that is not a Prometheus collector.
        // `$C.build()...register()` with the class unbound matches this.
        Report.build().name("monthly").register();

        // A simpleclient collector built and NOT registered: `.create()`. Reported as a
        // registered metric it would carry a `registry_bound: "yes"` the source contradicts.
        Histogram.build().name("unregistered").help("not scraped").create();
    }
}
