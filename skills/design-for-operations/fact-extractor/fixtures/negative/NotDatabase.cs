// In-memory collections. Measured defect: a DbSet rule constrained on a trailing
// `s` in the receiver name filed 59 of these on the .NET reference estate as database writes.
namespace Negative;

class NotDatabase
{
    void Collections(List<string> results, Response response, View view)
    {
        results.Add("x");
        results.Remove("x");
        response.Items.Add(new Item());
        view.Effects.Add(new Effect());
        view.GestureRecognizers.Add(new TapGestureRecognizer());
        var basketItems = new List<Item>();
        basketItems.Add(new Item());
        basketItems.RemoveRange(0, 1);
    }
}

// `Execute` and `ExecuteAsync` on things that are not connections. Measured defect
// Six of eight matches on the reference estate were these.
class NotCommands
{
    async Task Run(ICommand Command, ResiliencePipeline _pipeline, IExecutionStrategy strategy)
    {
        Command.Execute(null);
        await _pipeline.Execute(async () => { });
        await strategy.ExecuteAsync(async () => { });
    }
}
